from pdf import PDF
from article import ArticleSummary
import logging
from db import DB, Persistance 
from typing import List

class SearchResults:
    """
    SearchResults is a class holding configuration for search queries.

    Configuration
    - max_search_results: limit on the amount of search results
    """
    def __init__(self, max_search_results=10) -> None:
        self.max_search_results = max_search_results
        
class ResearchQueryEngine:
    """
    ResearchQueryEngine is an interface for engines. 
    """
    def search(self, keywords, search_params:SearchResults) -> List[ArticleSummary]:
        """
        search searches engines for results.

        Input 
        - keywords:         list of keywords (string) to search for.
        - search_params:    set of configuration for the search.
        
        Output 
        - List of ArticleSummary results.
        """
        raise Exception("Unimplemented search method")

class QueryEngineFactory:
    """
    QueryEngineFactory is a class responsible to create engines to be used for the search queries. 
    """    
    def __init__(self, db:DB, max_pages_processed:int, pdf:PDF = PDF()) -> None:
        self.db = db                                    # injection of the persistance layer 
                                                        # for operations such as saving the 
                                                        # article inside the db
        self.max_pages_processed = max_pages_processed  # stating how many pages to process
        self.pdf = pdf                                  # injection of the PDF operations, 
                                                        # such as summarize
    
    def engines(self) -> List[ResearchQueryEngine]:
        """
        A list of engines to be used.
        
        Output 
        - List classes that implement ResearchQueryEngine 
        """
        return [HistoricalQueryEngine(self.db),GoogleScholarQueryEngine(self.db, self.max_pages_processed, self.pdf)]

class QueryEngineController(ResearchQueryEngine):
    """
    QueryEngineController is a class responsible to orchestrate the search flow (i.e. calling engines)
    """
    def __init__(self, db:Persistance, execution_type:None, max_pages_processed = 10, pdf:PDF = PDF()) -> None:
        """
        Creates an instance of the QueryEngineController object.
        """
        self.engines = QueryEngineFactory(db, max_pages_processed, pdf).engines()
        if execution_type is None or execution_type == "scattergetter":
            self.article_search = self.__scattergetter
        elif execution_type == "priority":
            self.article_search = self.__priority_search
        else:
            self.article_search = self.__scattergetter

    def __priority_search(self, keywords, search_params:SearchResults):
        results = []
        for engine in self.engines:
            remaining_articles_count = search_params.max_search_results - len(results)
            [results.append(article) for article in engine.search(keywords, search_params)[:remaining_articles_count]]
            
            if len(results) >= search_params.max_search_results:
                logging.info(f"Gathered enough ({len(results)}) articles to query")
                break
        return results

    def __scattergetter(self, keywords, search_params:SearchResults):
        results = []
        for engine in self.engines:
            [results.append(article) for article in engine.search(keywords, search_params)]
        return results

    def search(self, keywords, search_params:SearchResults) -> List[ArticleSummary]:
        """
        search performs the search based on the keywords and search configuration provided. This function is the brain of the 
        search process, as it sends the request to all engines and then joins them to a single list of ArticleSummary objects.

        Input 
        - keywords:         list of keywords (string) to search for.
        - search_params:    set of configuration for the search.
        
        Output 
        - List of ArticleSummary results 
        """
        logging.info("Searching for keywords {keywords} in engines".format(keywords=keywords))
        results = self.article_search(keywords, search_params)
        logging.info("Found {result_count} search results for search query".format(result_count=len(results)))
        return results

class GoogleScholarQueryEngine(ResearchQueryEngine):
    """
    GoogleScholarQueryEngine is an `~engines.ResearchQueryEngine` implementation of Google Scholar API.
    """

    GS_URL = "https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q="

    def __init__(self, db:DB, max_pages_processed:int, pdf:PDF = PDF()):
        self.pdf = pdf
        self.db = db
        self.max_pages_processed = max_pages_processed

    def _compose_gs_url(self,keywords,extra_params,extra_search_param):
        query_params = '+'.join(keyword.replace(" ", '+') for keyword in keywords+extra_params).replace(" ", '')
        return self.GS_URL + query_params + extra_search_param

    def search(self, keywords, search_results:SearchResults) -> List[ArticleSummary]:
        article_summaries = []
        i=0
        
        # Query google until max results is reached
        while search_results.max_search_results > len(article_summaries):
            next_page="&start={i}".format(i=i)
            logging.info("Searching for results in page: {page}".format(page = int(i/10)))
            # Compose the page scrapping with pagination in mind
            url = self._compose_gs_url(keywords, ["filetype%3Apdf"], next_page)
            # Fetch for PDF URLs from the google scholar result
            urls_to_fetch = self.pdf.fetch_urls(url)
            if len(urls_to_fetch) == 0:
                logging.info(f"Search engine returned no results for query {url}")
                break
            # Process each article separately 
            for pdf_url_info in urls_to_fetch:

                if search_results.max_search_results - len(article_summaries) <= 0:
                    break

                # Only process the article if its a new one (i.e. not present in db)
                article_from_db = self.db.get_article_by_url(pdf_url_info[0])
                if article_from_db is not None:
                    article_summaries.append(article_from_db)
                    continue

                # Summarize PDF while extracting relevant information from it (like abstract, keywords)
                summarized_pdf = self.pdf.summarize(pdf_url_info[0], max_pages_processed = self.max_pages_processed )
                if summarized_pdf is None:
                    logging.warn("Ignoring this url {url} because it is not found.".format(url=pdf_url_info[0]))
                    continue
                
                # Compose an article summary which will be inserted into the db
                article_summary = ArticleSummary(
                        origin="googlescholar",
                        search_keywords = ",".join(keywords),
                        keywords = summarized_pdf.keywords,
                        title = pdf_url_info[1],
                        authors = pdf_url_info[2],
                        summary = summarized_pdf.summary,
                        future_work = summarized_pdf.future_work,
                        conclusions = summarized_pdf.conclusions,
                        url = pdf_url_info[0]
                    )
                article_summaries.append(article_summary)
                self.db.insert_article(article_summary)
            i = i + 10
        return article_summaries

class HistoricalQueryEngine(ResearchQueryEngine):
    """
    HistoricalQueryEngine is an engine which queries the DB for historical results.
    """
    def __init__(self, db:DB):
        self.db = db

    def search(self, keywords, search_results:SearchResults) -> List[ArticleSummary]:
        """
        Perform a db search for related historical articles based of the input keywords
        """
        return self.db.get_article_by_keywords(keywords, search_results.max_search_results)

class MockEngine(ResearchQueryEngine):
    """
    MockEngine is an engine for testing purposes.
    """
    def search(self, keywords,search_params) -> List[ArticleSummary]:
        return [
            {
                "title": "first fake title",
                "keywords":["key 1", "key2"],
                "authors":". Kyriakos Hadjicharalambous",
                "summary":"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ullamcorper dignissim cras tincidunt lobortis feugiat vivamus at augue. Gravida in fermentum et sollicitudin ac orci phasellus egestas tellus. Arcu felis bibendum ut tristique et. Metus aliquam eleifend mi in nulla posuere sollicitudin. Tortor posuere ac ut consequat semper viverra nam. Commodo sed egestas egestas fringilla. Ullamcorper eget nulla facilisi etiam dignissim diam quis. Sit amet nulla facilisi morbi tempus iaculis urna. Velit laoreet id donec ultrices tincidunt arcu non sodales neque. Nunc sed blandit libero volutpat sed.\n\
Et netus et malesuada fames ac turpis egestas. Enim ut sem viverra aliquet eget sit amet tellus cras. Ante metus dictum at tempor. Vitae sapien pellentesque habitant morbi tristique senectus. Velit laoreet id donec ultrices tincidunt arcu non. Dui accumsan sit amet nulla. Blandit massa enim nec dui nunc mattis enim ut tellus. Lacus luctus accumsan tortor posuere ac ut consequat semper viverra. Sed felis eget velit aliquet sagittis id. Ut eu sem integer vitae justo eget magna. Lacus sed turpis tincidunt id aliquet risus feugiat in. Sed vulputate odio ut enim blandit.\n\
Massa vitae tortor condimentum lacinia quis vel eros. Ullamcorper a lacus vestibulum sed arcu. Velit laoreet id donec ultrices tincidunt arcu. Amet nisl purus in mollis nunc. Id faucibus nisl tincidunt eget nullam non nisi. Gravida neque convallis a cras semper auctor neque vitae. Dis parturient montes nascetur ridiculus mus mauris. Lobortis elementum nibh tellus molestie nunc non blandit massa. Massa placerat duis ultricies lacus sed turpis tincidunt. Augue interdum velit euismod in pellentesque massa placerat duis ultricies. Consectetur libero id faucibus nisl tincidunt eget nullam non. Nulla pharetra diam sit amet nisl. Amet est placerat in egestas erat imperdiet sed euismod nisi. Mattis molestie a iaculis at erat pellentesque adipiscing commodo. Turpis massa tincidunt dui ut ornare lectus sit amet est.\n\
Tortor pretium viverra suspendisse potenti nullam ac. In est ante in nibh mauris. Fusce ut placerat orci nulla pellentesque dignissim enim sit. Quisque sagittis purus sit amet volutpat consequat mauris. Arcu non odio euismod lacinia at quis risus se",
                "future_work":"Velit laoreet id donec ultrices tincidunt arcu non sodales neque. Nunc sed blandit libero volutpat sed.\n\
Et netus et malesuada fames ac turpis egestas. Enim ut sem viverra aliquet eget sit amet tellus cras. ",
                "conclusions":"aying out pages with meaningless filler text can be very useful when the focus is meant to be on design, not content.\m\
The passage experienced a surge in popularity during the 1960s when Letraset used it on their dry-transfer sh",
                "url":"http://link.to.first.pdf",
            },
            {
                "title": "second fake title",
                "keywords":["key 3", "key2"],
                "authors":". Hadjicharalambous Kyriakos",
                "summary":"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ullamcorper dignissim cras tincidunt lobortis feugiat vivamus at augue. Gravida in fermentum et sollicitudin ac orci phasellus egestas tellus. Arcu felis bibendum ut tristique et. Metus aliquam eleifend mi in nulla posuere sollicitudin. Tortor posuere ac ut consequat semper viverra nam. Commodo sed egestas egestas fringilla. Ullamcorper eget nulla facilisi etiam dignissim diam quis. Sit amet nulla facilisi morbi tempus iaculis urna. Velit laoreet id donec ultrices tincidunt arcu non sodales neque. Nunc sed blandit libero volutpat sed.\n\
Et netus et malesuada fames ac turpis egestas. Enim ut sem viverra aliquet eget sit amet tellus cras. Ante metus dictum at tempor. Vitae sapien pellentesque habitant morbi tristique senectus. Velit laoreet id donec ultrices tincidunt arcu non. Dui accumsan sit amet nulla. Blandit massa enim nec dui nunc mattis enim ut tellus. Lacus luctus accumsan tortor posuere ac ut consequat semper viverra. Sed felis eget velit aliquet sagittis id. Ut eu sem integer vitae justo eget magna. Lacus sed turpis tincidunt id aliquet risus feugiat in. Sed vulputate odio ut enim blandit.\n\
Massa vitae tortor condimentum lacinia quis vel eros. Ullamcorper a lacus vestibulum sed arcu. Velit laoreet id donec ultrices tincidunt arcu. Amet nisl purus in mollis nunc. Id faucibus nisl tincidunt eget nullam non nisi. Gravida neque convallis a cras semper auctor neque vitae. Dis parturient montes nascetur ridiculus mus mauris. Lobortis elementum nibh tellus molestie nunc non blandit massa. Massa placerat duis ultricies lacus sed turpis tincidunt. Augue interdum velit euismod in pellentesque massa placerat duis ultricies. Consectetur libero id faucibus nisl tincidunt eget nullam non. Nulla pharetra diam sit amet nisl. Amet est placerat in egestas erat imperdiet sed euismod nisi. Mattis molestie a iaculis at erat pellentesque adipiscing commodo. Turpis massa tincidunt dui ut ornare lectus sit amet est.\n\
Tortor pretium viverra suspendisse potenti nullam ac. In est ante in nibh mauris. Fusce ut placerat orci nulla pellentesque dignissim enim sit. Quisque sagittis purus sit amet volutpat consequat mauris. Arcu non odio euismod lacinia at quis risus se",
                "future_work":"Velit laoreet id donec ultrices tincidunt arcu non sodales neque. Nunc sed blandit libero volutpat sed.\n\
Et netus et malesuada fames ac turpis egestas. Enim ut sem viverra aliquet eget sit amet tellus cras. ",
                "conclusions":"aying out pages with meaningless filler text can be very useful when the focus is meant to be on design, not content.\m\
The passage experienced a surge in popularity during the 1960s when Letraset used it on their dry-transfer sh",
                "url":"http://link.to.second.pdf",
            }
        ]