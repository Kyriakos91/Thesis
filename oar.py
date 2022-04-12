import logging
from  bot import ChatbotFactory
from flask import Flask, render_template, request, jsonify, send_from_directory
from engines.engine import QueryEngineController, SearchResults
from logs import initialize_logger
from db import DB
from pdf import PDF, PDFMuPDFEngine, PDFMinerEngine, PDFReadStrategyAll, PDFReadStrategyPortion, PYPDF2Engine
from permission import PermissionFactory, PermissionErrorException, PermissionResponse
from multiprocessing import cpu_count

HOME_PAGE = "chat.html"

def __get_log_level_from_config(level:str) -> int:
    sanitized_level = level.strip().lower()
    default = logging.INFO
    if sanitized_level == "info":
        default = logging.INFO
    elif sanitized_level == "error":
        default = logging.ERROR
    elif sanitized_level == "warn":
        default = logging.WARN
    elif sanitized_level == "debug":
        default = logging.DEBUG
    elif sanitized_level == "critical":
        default = logging.CRITICAL
    return default
    
def create_app():
    """
    create_app initializes backend and registers endpoints.
    
    backend configuration reside in config_[ENVTYPE].py file, where
    ENVTYPE can be dev or prod. this file must exist for the backend
    to load successfully.
    """
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    logger = initialize_logger(loginfo=__get_log_level_from_config(\
        app.config['BACKEND_LOG_LEVEL']))
    db = DB(app.config['SQLALCHEMY_DATABASE_URI'])

    parallelism = app.config['PDF_MULTIPROCESSING_PARALLELISM_COUNT']
    if parallelism <= 0:
        parallelism = cpu_count()
    
    engine = app.config['PDF_ENGINE'].strip().lower()
    if engine == "pymu":
        engine = PDFMuPDFEngine()
    elif engine == "pdf2":
        engine = PYPDF2Engine()
    else:
        engine = PDFMinerEngine()

    strategy = app.config['PDF_PAGE_READ_STRATEGY'].strip().lower()
    if strategy == "portion":
        strategy = PDFReadStrategyPortion(app.config['PDF_PORTION_BEGINING_COUNT'], app.config['PDF_PORTION_ENDING_COUNT'])
    else:
        strategy = PDFReadStrategyAll()

    pdf = PDF(processes_per_search=parallelism, multiprocessing=app.config['PDF_MULTIPROCESSING_ENABLED'], engine=engine, strategy=strategy)
    bot = ChatbotFactory().create_bot(app.config['BOT_NAME'], \
        app.config['BOT_CORPUS_DATA_DIR'], db, app.config['BOT_CONFIDENCE_THRESHOLD'], not app.config['BOT_LEARN_FROM_CHAT'])
    query_controller = QueryEngineController(db, app.config['ENGINE_EXECUTION_MODEL'],app.config['ENGINE_MAX_PAGES_PROCESS'], pdf)
    max_results = app.config['ENGINE_MAX_UI_RESULTS']
    permissions = PermissionFactory().create(
        app.config['BACKEND_PERMISSION_POLICY'], 
        app.config['BACKEND_PERMISSION_TTL'], 
        app.config['BACKEND_TOTAL_SEARCH_ATTEMPTS'])

    # Endpoint for getting fields
    @app.route("/fields")
    def fields():
        """
        GET endpoint to get fields content and expose them to the user
        """
        try:
            logger.debug("Received a request for fields content")
            return jsonify({'fields': db.get_fields()})
        except Exception as e:
            logger.error(f"Error while getting fields' content. Error: {e}")
            return jsonify({'status':'ERROR'})

    # Endpoint for getting webpage
    @app.route("/")
    def home():
        """
        GET endpoint to get HTML page content
        """
        try:
            logger.debug("Received a request for HTML page content")
            return render_template(HOME_PAGE)
        except Exception as e:
            logger.error(f"Error while getting HTML Content. Error: {e}")
            return jsonify({'error':True})

    # Endpoint for getting resources
    @app.route('/static/<path:path>')
    def send_js(path):
        """
        GET endpoint to get resources for the HTML page (such as js, css)
        """
        try:
            return send_from_directory('static', path)
        except Exception as e:
            logger.error(f"Error while getting resource {path} Content. Error: {e}")
            return jsonify({'error':True})

    # Endpoint for training the chatbot
    @app.route("/train")
    def train():
        """
        GET endpoint to train the model
        """
        try:
            logger.debug("Received a request for bot training")
            __check_permission(permissions.can_train, request.access_route[-1])
            train_result = bot.train()
            return jsonify({'status':train_result.success, 'error':False})
        except PermissionErrorException as p:
            logger.error(f"Error while searching with the keywords the user wants. Error: {p}")
            return jsonify({'status':"train limit reached", 'error':True})
        except Exception as e:
            logger.error(f"Error while training the bot. Error: {e}")
            return jsonify({'error':True})

    # Endpoint for communicating with the chatbot
    @app.route("/ask", methods=['POST'])
    def ask():
        """
        POST endpoint for querying the model with a message.

        The body should contain `messageText` with the message.
        """
        try:
            logger.debug("Received a request for chat response for the bot")
            __check_permission(permissions.can_ask, request.access_route[-1])
            message = str(request.form['messageText'].lower().strip())
            response = bot.ask(message)
            response = jsonify({
                'error':False,
                'answer': response.answer,
                'captured_domains':response.captured_domains
            })

            logging.debug(f"Server response for {message} is {response.__dict__}")
            return response
        except PermissionErrorException as p:
            logger.error(f"Error while searching with the keywords the user wants. Error: {p}")
            return jsonify({
                'error':False,
                'answer': "I am sorry, search is limited, please try again later!",
                'captured_domains':[]
            })

        except Exception as e:
            logger.error(f"Error while asking the bot for response. Error: {e}")
            return jsonify({'error':True})

    # Endpoint for performing a search
    @app.route("/search", methods=['POST'])
    def search():
        """
        POST endpoint for article searching.

        """
        try:
            logger.debug("Received a request for search response.")
            __check_permission(permissions.can_search, request.access_route[-1])
            keywords = request.form.getlist("keywords[]")
            articles_summaries =  __execute_query(keywords)
            response = jsonify({
                'error':False,
                'has_articles': articles_summaries is not None and len(articles_summaries) > 0,
                'articles':[article.__dict__ for article in articles_summaries],
                'had_error':False,
                'original_message': keywords
            })
            logging.debug(f"Server response for {keywords} is {response.__dict__}")
            return response

        except PermissionErrorException as p:
            logger.error(f"Error while searching with the keywords the user wants. Error: {p}")
            return jsonify({
                'error':False,
                'has_articles': False,
                'articles':[],
                'had_error':False,
                'original_message': keywords
            })
        except Exception as e:
            logger.error(f"Error while searching with the keywords the user wants. Error: {e}")
            return jsonify({'error':True})

    def __execute_query(keywords):
        query_result = query_controller.search(keywords, search_params=SearchResults(max_search_results=max_results))
        return query_result

    def __check_permission(api_type, user):
        result:PermissionResponse = api_type(user)
        logging.debug(f"Response from permission check: {result.__dict__}")
        if not result.can_perform:
            raise PermissionErrorException(
                user=user, 
                method=result.operation_name, 
                attempts=result.current_attempts,
                time_until_expiration_in_seconds=result.ttl_left)

    return app

if __name__ == "__main__":
    app=create_app()
    app.run()
  
