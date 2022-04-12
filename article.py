from datetime import datetime

class ArticleSummary:
    """
    ArticleSummary is a DTO (Data Transfer Object) containing information about extracted articles. 

    The required fields are origin (source of extraction, i.e. google scholar), url (link to the article) and keywords (that caught this article).
    All other information are optional and if they were unable to get parsed, will remain empty.
    """
    def __init__(self, origin, url,search_keywords="", keywords="", date=datetime.now(), title="", authors="",\
         summary="", future_work="", conclusions="") -> None:
        self.origin = origin 
        self.url = url
        self.date=date
        self.search_keywords = search_keywords
        self.keywords = keywords
        self.title = title
        self.authors = authors
        self.summary = summary
        self.future_work = future_work 
        self.conclusions = conclusions