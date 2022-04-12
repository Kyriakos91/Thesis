import string
import os
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from scrapper import FieldScrapper
from corpus_creator import CorpusCreator, Field
import logging
from db import DB
from typing import List

CANT_FIND_AN_ANSWER_MESSAGE = "Sorry i have no idea about that."
REFETCH_DOMAINS = True

class BotAskResponse:
    """
    Bot response when asked a question.
    """
    def __init__(self, answer:string, captured_domains:List[str] = None) -> None:
        self.answer = answer
        self.captured_domains = captured_domains
        if captured_domains is None:
            self.captured_domains = []

class BotTrainResponse:
    """
    Bot response when trained.
    """
    def __init__(self, success:bool) -> None:
        self.success = success

class Bot:
    """
    Entity that interacts with the user for domain discovery and article summaries.

    In order to become one, one must implement ask (given a message, return an answer) and train (improve model based on domain discovery).
    """
    def ask(self, message:string) -> BotAskResponse:
        """
        Asking a bot with a message.

        Input 
        - message: text from the user of type string.
        
        Output 
        - BotAskResponse containing relevant reply from the bot.
        """
        raise Exception("Unimplemented method")

    def train(self, reload=REFETCH_DOMAINS) -> BotTrainResponse:
        """
        Training a model based on existing data.

        Input 
        - reload: whether to scrape for fields.
        
        Output 
        - BotTrainResponse containing whether the train succeeded or failed.
        """
        raise Exception("Unimplemented method")

class ChatbotFactory:
    """
    Factory for implementation of chatbots.
    """
    def create_bot(self, name, datadir, db, confidence_threshold, read_only) -> Bot:
        """
        create_bot factory method that returns an object implementing bot interface.

        Input 
        - name    : name of the bot for UI
        - datadir : location of the data required to train the model
        
        Output 
        - Instance of a Bot object
        """
        return ChatterBotWrapper(name, datadir, db, response_minimum_confidence_score=confidence_threshold, read_only=read_only)

class ChatterBotWrapper(Bot):
    """
    Bot implementation of Chatterbot package.

    We are using Chatterbot both for training the model based on scrapped fields from Wikipedia as well as for interacting with the user.

    Configuration 
    - bot_response_retry_count:             how many times to try to get a response from the bot when confidence score is lower the threshold
    - response_minimum_confidence_score:    confidence threshold score
    """
    def __init__(self, name, datadir, db:DB, bot_response_retry_count = 1, response_minimum_confidence_score = 0.1, 
    logic_adapters = ['best_match.BestMatchWithConfidence'], read_only=True):

        self.name = name
        self.bot = ChatBot(name, logic_adapters = logic_adapters,read_only=read_only)
        self.trainer = ChatterBotCorpusTrainer(self.bot)
        self.datadir = datadir
        self.bot_response_retry_count = bot_response_retry_count
        self.response_minimum_confidence_score = response_minimum_confidence_score
        self.fields:List[Field] = []
        self.db = db

    def ask(self, message) -> BotAskResponse:
        try:
            counter = self.bot_response_retry_count
            while counter != 0:
                logging.info("Asking ({retry}/{total}) the bot with message {message}"\
                    .format(retry=self.bot_response_retry_count-counter, total=self.bot_response_retry_count, message=message))
                # send a message to the chatbot and get a response. The response will be the answer
                # back to the user with level of confidence which states how certain the bot is with
                # his message back to the user
                response = self.bot.get_response(message)
                logging.info(f"Bot replied with message {response.__dict__} and confidence score of {response.confidence}" )
                # In case the confidence score is lower than the defined threshold, it will retry
                if response.confidence < self.response_minimum_confidence_score:
                    logging.info("Score is below threshold, retrying...")
                    counter = counter - 1
                else:
                    # The message back will contains also the captured domains from the bot's response. 
                    # This will be used by the user to later on select which domains he would like to
                    # us and get articles from. For example, if the conversation picked up 'computer science' 
                    # as a possible domain, the user can later on select it and the system will search for 
                    # articles with the 'computer science' as a search key word
                    cleanzed_message = self.__prepare_message_for_domain_discovery(message)
                    captured_domains = []
                    if len(self.fields) == 0:
                        self.__repload_fields()
                    for f in self.fields:
                        captured_domains.extend([domain.name for domain in f.get_domain(cleanzed_message)])
                    return BotAskResponse(answer=str(response), captured_domains=captured_domains)
            logging.warn("Did not find a match for the message, returning a default answer")
            return BotAskResponse(answer=CANT_FIND_AN_ANSWER_MESSAGE)
        except IndexError as error:
            logging.error(f"Failed asking the bot with a message, returning a default answer. Error: {error}")
            return BotAskResponse(answer=CANT_FIND_AN_ANSWER_MESSAGE)

    def train(self, reload=REFETCH_DOMAINS) -> BotTrainResponse:
        """
        Training the model with the option of scrapping (reload).
        """
        logging.info(f"About to train the model. Reload option is {reload}")
        try:
            if reload:
                self.__reload_corpus()                  # field scraping
            for file in os.listdir(self.datadir):       # get all corpuses
                file_path = str(self.datadir + file)
                self.trainer.train(file_path)           # train them with the bot
            logging.info("Model training successful")
            return BotTrainResponse(success=True)
        except Exception as e:
            logging.error(f"Model training failed. Error: {e}")
            return BotTrainResponse(success=False)
    
    def __reload_corpus(self) -> bool:
        try:
            self.__repload_fields()
            corpus_creator = CorpusCreator(self.datadir)
            corpus_creator.create(self.fields)
            if self.db is not None and len(self.fields) > 0:
                string_fields = [field.name for field in self.fields]
                self.db.insert_fields(string_fields)
            logging.info("Reloading corpus was successful")
            return True
        except Exception as e:
            logging.error(f"Reloading corpus failed. Error: {e}")
            return False

    def __repload_fields(self) -> None:
        try:
            fieldscrapper = FieldScrapper()
            self.fields = fieldscrapper.scrape()
        except Exception as e:
            logging.error(f"Unable to scrape for fields (this means functionality will get impacted). Error: {e}")
            return False
        
    def __prepare_message_for_domain_discovery(self, message):
        # Can be optimized
        mapping = { '!':' ', '@':' ', '#':' ', '$':' ', '%':' ', \
                    '^':' ', '&':' ', '*':' ', '(':' ', ')':' ', '-':' ', \
                    ':':' ', ',':' ', '.':' ', ';':' ', '\\':' ', '/':' ', \
                    '?':' ', '{':' ', '}':' ', '<':' ', '>':' ', '|':' ', \
                    '"':' ', '~':' ', '±':' ', '§':' ', '_':' ', '=':' ', \
                         '+':' ', '\'':' ', '[':' ', ']':' '}
        for k, v in mapping.items():
            message = message.replace(k, v)
        return message.strip()
