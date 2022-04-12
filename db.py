import logging
from sqlalchemy import *
import sqlalchemy
from article import ArticleSummary
from typing import List

class Persistance:
    """
    Interface for persistance operations 
    """
    def insert_article(self, article : ArticleSummary) -> bool:
        """ Insert new articles """
        raise Exception("Unimplemented method")
    def insert_fields(self, fields) -> bool:
        """ Insert new fields """
        raise Exception("Unimplemented method")
    def get_fields(self):
        """ Getting persisted fields """
        raise Exception("Unimplemented method")
    def get_article_by_url(self, url) -> ArticleSummary:
        """ Getting article based on url (PK) """
        raise Exception("Unimplemented method")
    def get_article_by_keywords(self, keywords:List[str], limit) -> ArticleSummary:
        """ Getting article based on searched key words """
        raise Exception("Unimplemented method")

class MockDB(Persistance):
    def __init__(self, insert_article_response="", insert_fields_response="",\
        get_fields_response="", get_article_by_url_response="", get_article_by_keywords="response") -> None:
        
        self.insert_article_response = insert_article_response
        self.insert_fields_response = insert_fields_response
        self.get_fields_response = get_fields_response
        self.get_article_by_url_response = get_article_by_url_response
        self.get_article_by_keywords = get_article_by_keywords
        super().__init__()
        
    def insert_article(self, article : ArticleSummary) -> bool:
        return self.insert_article_response
    def insert_fields(self, fields) -> bool:
        return self.insert_fields_response
    def get_fields(self):
        return self.get_fields_response
    def get_article_by_url(self, url) -> ArticleSummary:
        return self.get_article_by_url_response
    def get_article_by_keywords(self, keywords:List[str], limit) -> ArticleSummary:
        return self.get_article_by_keywords


class DB(Persistance):
    """
    ArticleDB is a DAL (Data Access Layer) responsible for the persistency of processed articles.
    """
    def __init__(self, database_uri = 'sqlite:///db.sqlite3'):
        """
        Creating of the ArticleDB class.

        On creation, this entity also checks connection to the database, as well as makes sure that the articles table 
        exists, if not, it creates it.

        Configuration 
        - database_uri: connection string to the database
        """
        self.database_uri = database_uri
        self.__create_tables()

    def __create_tables(self) -> None:
        engine = create_engine(self.database_uri)
        metadata = MetaData()
        self.article_table = self.__get_article_table(metadata=metadata)
        self.fields_table = self.__get_fields_table(metadata=metadata)
        metadata.create_all(engine)

    def __get_article_table(self, metadata = MetaData()) -> Table:
        return Table('articles', metadata,
                    Column('origin', String(255), default="N/A"),
                    Column('url', Text(), default="N/A", primary_key=True),
                    Column('date', DateTime()),
                    Column('search_keywords', Text(), default="N/A"),
                    Column('keywords', Text(), default="N/A"),
                    Column('title', Text(), default="N/A"),
                    Column('authors', Text(), default="N/A"),
                    Column('summary', Text(), default="N/A"),
                    Column('conclusions', Text(), default="N/A"),
                    Column('future_work', Text(), default="N/A"))

    def __get_fields_table(self, metadata = MetaData()) -> Table:
        return Table('fields', metadata,
                    Column('field', Text(), default="N/A", primary_key=True)
                    )

    def insert_article(self, article : ArticleSummary) -> bool:
        """
        insert_article inserts an article to the database. 

        This function encapsulates errors (for instance, when there is a violation of integrity of primary key).

        Input 
        - article: the article to persist. 

        Output
        - boolean representing whether the article was persisted or not.
        """
        try:
            logging.info(f"About to persist article to the db. Article:\n {article.__dict__}")
            query = insert(self.article_table) 
            engine = create_engine(self.database_uri)
            connection = engine.connect()
            values_list = [article.__dict__]
            connection.execute(query,values_list)
            logging.info("Persisting article to the database was successful")
            return True
        except sqlalchemy.exc.IntegrityError as ie:
            logging.error("The article with url: {article} cannot inserted to the database because key already exists. Error: {ie}".format(article=article.url, ie=ie))
            return False
        except Exception as e:
            logging.error("The article with url: {article} cannot inserted to the database. Error: {e}".format(article=article.url, e=e))
            return False

    def insert_fields(self, fields) -> bool:
        """
        insert_fields inserts fields to the database. 

        Input 
        - fields: list of string fields

        Output
        - boolean representing whether the fields were persisted or not.
        """
        try:
            # can be optimized with native SQL query (INSERT... WHERE ...)
            persisted_fields = [row[0] for row in self.get_fields()]
            fields_to_insert = []
            for f in set(fields):
                if f not in persisted_fields and f != "":
                    fields_to_insert.append(f)

            if len(fields_to_insert) == 0:
                logging.info(f"There are no new fields to insert.")
                return True

            logging.info(f"About to persist {len(fields_to_insert)} fields to the db.")
            query = insert(self.fields_table) 
            engine = create_engine(self.database_uri)
            connection = engine.connect()
            connection.execute(query,[{"field": field} for field in fields_to_insert])
            logging.info("Persisting fields to the database was successful.")
            return True
        except sqlalchemy.exc.IntegrityError as ie:
            logging.error(f"The fields couldn't be inserted to the database because key already exists. Error: {ie}")
            return False
        except Exception as e:
            logging.error(f"The fields couldn't be inserted to the database. Error: {e}")
            return False

    def get_article_by_url(self, url) -> ArticleSummary:
        """
        get_article_by_url gets an article based on the url (primary key).
        Input 
        - url: the URL of the article.
        Output
        - ArticleSummary object if found, None if not.
        """
        try:
            article_exists = select([self.article_table]).where(self.article_table.columns.url == url)
            engine = create_engine(self.database_uri)
            connection = engine.connect()

            rows = connection.execute(article_exists).fetchall()

            if len(rows) == 0:
                return None
            else:
                article_db = ArticleSummary(origin=rows[0][0],
                url = rows[0][1],
                date = rows[0][2],
                search_keywords = rows[0][3],
                keywords = rows[0][4],
                title = rows[0][5],
                authors = rows[0][6],
                summary = rows[0][7],
                conclusions = rows[0][8],
                future_work = rows[0][9]
                )
                return article_db
                
        except Exception as e:
            logging.error("Database cannot get the article by url: {url}. Error: {e}".format(url=url, e=e))
            return None

    def get_article_by_keywords(self, keywords:List[str], limit = 10) -> ArticleSummary:
        """
        get_article_by_url gets an article based on the url (primary key).

        Input 
        - url: the URL of the article.

        Output
        - ArticleSummary object if found, None if not.
        """
        try:
            matching_articles = select([self.article_table])
            for keyword in keywords:
                matching_articles = matching_articles.where(self.article_table.columns.search_keywords.like(f"%{keyword}%"))

            matching_articles = matching_articles.limit(limit)

            engine = create_engine(self.database_uri)
            connection = engine.connect()

            rows = connection.execute(matching_articles).fetchall()

            return [self.__convert_row_to_article_summary(row) for row in rows]            
                
        except Exception as e:
            logging.error("Database cannot get the article by url: {url}. Error: {e}".format(url=url, e=e))
            return None

    def __convert_row_to_article_summary(self, row):
        return ArticleSummary(origin=row[0],
                url = row[1],
                date = row[2],
                search_keywords = row[3],
                keywords = row[4],
                title = row[5],
                authors = row[6],
                summary = row[7],
                conclusions = row[8],
                future_work = row[9])

    def get_fields(self):
        """
        get_fields gets all the fields in the db.

        Output
        - String array of all the fields
        """
        try:
            article_exists = select([self.fields_table])
            engine = create_engine(self.database_uri)
            connection = engine.connect()
            return connection.execute(article_exists).fetchall()

        except Exception as e:
            logging.error(f"Database cannot get all fields. Error: {e}")
            return []
