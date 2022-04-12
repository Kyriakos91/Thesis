from math import ceil
from operator import concat
import os
from datetime import datetime
from fileinput import filename
from struct import pack
from urllib.error import HTTPError
import requests
from bs4 import BeautifulSoup
import urllib.request
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfpage import PDFPage
from io import StringIO
import re
import logging 
from multiprocessing import Pool, cpu_count, pool
from PyPDF2 import PdfFileReader
import fitz
from typing import List 
import json

class PDFReadStrategy:
     def pick_pages(self, pages):
          raise Exception("Unimplemented Exception")

class PDFReadStrategyAll:
     def pick_pages(self, pages):
          return pages

class PDFReadStrategyPortion:
     def __init__(self, start=33, end=33) -> None:
         self.start = start
         self.end = end

     def pick_pages(self, pages):
          start = ceil(len(pages) * self.start / 100)
          end = ceil(len(pages) * self.end / 100)
          return pages[:start] + pages[end*-1:]

class PDFEngine:
     """
     Abstraction of a PDF Mining Engine that gets PDF file and return its content
     """
     def get_pdf_content(self,filename, max_pages_processed, pool, multiprocessing, strategy):
          raise Exception ("Unimplemented method")

class PYPDF2Engine(PDFEngine):
     """
      PYPDF2Engine implementation of the PDFEngine interface
     """
     def get_pdf_content(self,filename, max_pages_processed, pool, multiprocessing, strategy):
          try:
               # Opening the PDF files as a byte of streams and feed it to the reader
               pdfFileObj = open(filename,'rb')
               pdfFile = PdfFileReader(pdfFileObj)
               # Create page/index page for paralllel processing
               index_page_pair = [(index, filename) for index in range(min(pdfFile.getNumPages(), max_pages_processed))]
               index_page_pair = strategy.pick_pages(index_page_pair)
               merged_output = StringIO()

               # In case of multi processing, create a process per page and get its content
               if multiprocessing:
                    res = pool.starmap(get_pdf2_page, index_page_pair)
                    def getKey(item):
                         return item[1]
                    sorted(res, key=getKey)
                    [merged_output.write(part[0]) for part in res]
               else: # In case we want to use a single thread, read every page synchroniously 
                    for index, filename in index_page_pair:
                         merged_output.write(pdfFile.getPage(index).extractText())
               # Close the PDF file and return the content
               pdfFileObj.close()     
               return merged_output.getvalue()

          except Exception as e:
               logging.error("Cannot convert PDF: {filename} into text. Error: {e}".format(filename=filename, e=e))
               return None

class PDFMuPDFEngine(PDFEngine):

     ENCODING = "UTF-8"

     def SortBlocks(blocks):
          sblocks = []
          for b in blocks:
               x0 = str(int(b["bbox"][0]+0.99999)).rjust(4,"0") # x coord in pixels
               y0 = str(int(b["bbox"][1]+0.99999)).rjust(4,"0") # y coord in pixels
               sortkey = y0 + x0                                # = "yx"
               sblocks.append([sortkey, b])
          sblocks.sort()
          return [b[1] for b in sblocks] # return sorted list of blocks

     def SortLines(lines):
          slines = []
          for l in lines:
               y0 = str(int(l["bbox"][1] + 0.99999)).rjust(4,"0")
               slines.append([y0, l])
          slines.sort()
          return [l[1] for l in slines]

     def SortSpans(spans):
          sspans = []
          for s in spans:
               x0 = str(int(s["bbox"][0] + 0.99999)).rjust(4,"0")
               sspans.append([x0, s])
          sspans.sort()
          return [s[1] for s in sspans]


     def get_pdf_content(self,filename, max_pages_processed, pool, multiprocessing, strategy):
          try:
               pdfPages = fitz.open(filename)
               pair = [(index, filename) for index in range(min(len(pdfPages), max_pages_processed))]
               index_page_pair = strategy.pick_pages(pair)
               merged_output = StringIO()

               if multiprocessing:
                    res = pool.starmap(get_pymupdf_page, index_page_pair)
                    def getKey(item):
                         return item[1]
                    sorted(res, key=getKey)
                    [merged_output.write(part[0].getvalue()) for part in res]

               else:
                    for index, filename in index_page_pair:
                         page_text = pdfPages[index].get_text("json")
                         pgdict = json.loads(page_text)                    # create a dict out of it
                         blocks = self.SortBlocks(pgdict["blocks"])        # now re-arrange ... blocks
                         for b in blocks:
                              lines = self.SortLines(b["lines"])            # ... lines
                              for l in lines:
                                   spans = self.SortSpans(l["spans"])        # ... spans
                                   for s in spans:
                                        # ensure that spans are separated by at least 1 blank
                                        # (should make sense in most cases)
                                        if pg_text.endswith(" ") or s["text"].startswith(" "):
                                             pg_text += s["text"]
                                        else:
                                             pg_text += " " + s["text"]
                                   pg_text += "\n"                      # separate lines by newline

                         pg_text = pg_text.encode("UTF-8", "ignore")
                         merged_output.write(pg_text)
               
               return merged_output.getvalue()
          except Exception as e:
               logging.error("Cannot convert PDF: {filename} into text. Error: {e}".format(filename=filename, e=e))
               return None

class PDFMinerEngine(PDFEngine):
     def get_pdf_content(self,filename, max_pages_processed, pool, multiprocessing, strategy):
          try:
               pdfFile = open(filename,'rb')
               pages = list(PDFPage.get_pages(pdfFile,pagenos=set(),maxpages=0,password='',caching=True,check_extractable=True))
               index_page_pair = [(index, filename) for index in range(min(len(pages), max_pages_processed))]
               index_page_pair = strategy.pick_pages(index_page_pair)
               merged_output = StringIO()

               if multiprocessing:
                    res = pool.starmap(get_pdf_page, index_page_pair)
                    def getKey(item):
                         return item[1]
                    sorted(res, key=getKey)
                    [merged_output.write(part[0].getvalue()) for part in res]

               else:
                    resource_manager = PDFResourceManager(caching=True)
                    laParams = LAParams()
                    text_converter = TextConverter(resource_manager,merged_output,laparams=laParams)
                    interpreter = PDFPageInterpreter(resource_manager,text_converter)
                    for index, filename in index_page_pair:
                         interpreter.process_page(pages[index])
               pdfFile.close()     
               return merged_output.getvalue()
          except Exception as e:
               logging.error("Cannot convert PDF: {filename} into text. Error: {e}".format(filename=filename, e=e))
               return None




class PDF:
     """
     PDF is a class responsible to download and read PDF files (mainly for the articles).
     """
     ABSTRACT_REGEX = [
          (r'[A][Bb][Ss][Tt][Rr][Aa][Cc][Tt][ \n]{1,}(.+?)(?=\n\n|Keywords)', re.DOTALL),
          (r'[A][Bb][Ss][Tt][Rr][Aa][Cc][Tt](.+?)(?=\n ?\n ?Key ?W?w?ords?)', re.DOTALL),
          (r'[A][Bb][Ss][Tt][Rr][Aa][Cc][Tt][ \n]?(.+?)(?=\n\n)', re.DOTALL)
          ]

     KEYWORDS_REGEX = [
               (r'[K][Ee][Yy][ ]?[ ]?[Ww][Oo][Rr][Dd][Ss]? ?:? +(.+?)(?=\n +\n)', re.DOTALL),
               (r'[K][Ee][Yy][ ]?[ ]?[Ww][Oo][Rr][Dd][Ss]?[:]?.*?\n{0,}(.+?)(?=\n\n)', re.DOTALL),
               (r'[I][Nn][Dd][Ee][Xx][ ][Tt][Ee][Rr][Mm][Ss]?(.*?)(?=\n\n)', re.DOTALL)
               ]   

     CONCLUSION_REGEX = [
          (r'[C][Oo][Nn][Cc][Ll][Uu][Ss][Ii][Oo][Nn][Ss]?.*?\n{1,2}?(.+?)(?=\n ?\n ?\n?(\w+) {0,}\n)', re.DOTALL),
          (r'[Cc][Oo][Nn][Cc][Ll][Uu][Ss][Ii][Oo][Nn][Ss]?.*?\n{1,}(.+?)(?=\n ?\n ?\n?|\w+ {0,}\n)', re.DOTALL),
          (r'[Cc][Oo][Nn][Cc][Ll][Uu][Ss][Ii][Oo][Nn][Ss]?.*?[ \n]{4,}(.+?)(?=\n ?\n ?\n?(\w+) {0,}\n)', re.DOTALL),
          (r'[Cc][Oo][Nn][Cc][Ll][Uu][Ss][Ii][Oo][Nn][Ss]?.*?\n{1,}(.+?)(?=\n ?\n ?\n?)', re.DOTALL)
          ]
          
     FUTURE_WORK_REGEX = [
          (r'[Ff][Uu][Tt][Uu][Rr][Ee][ ][Ww][Oo][Rr][Kk][ \n]{1,}(.+?)(?=\n\n)', re.DOTALL),
          (r'[F][Uu][Tt][Uu][Rr][Ee][ ][Dd][Ii][Rr][Ee][Cc][Tt][Ii][Oo][Nn][Ss].+?\n{2,}(.+?)(?=\n\n(\w+)\n)', re.DOTALL),
          (r'[F][Uu][Tt][Uu][Rr][Ee][ ][Ss][Cc][Oo][Pp][Ee](.+?)\n{2,}(.?)(?=\n\n(\w+ )\n|CONCLUSION)', re.DOTALL),
          (r'[Ff][Uu][Tt][Uu][Rr][Ee]\n?\n?[Rr][Ee][Ss][Ee][Aa][Rr][Cc][Hh](.*?){1,}(.+?)(?=\n\n\w+\n)', re.DOTALL),
          (r'[Ff][Uu][Tt][Uu][Rr][Ee][ ][Ss][Tt][Uu][Dd][Ii][Ee][Ss].*?\n{1,2}?(.+?)(?=\n ?\n ?\n?(\w+) {0,}\n)', re.DOTALL)
          ]

     DEFAULT = "N/A"

     def __init__(self, processes_per_search=cpu_count(), multiprocessing:bool=False, engine=PDFMinerEngine(), strategy:PDFReadStrategy=PDFReadStrategyAll()) -> None:
          """
          Creating of the PDF class.

          Configuration 
          - processes_per_search:  sets the amount of parallelism (processes) when processing PDF files.
          """
          self.processes_per_search = processes_per_search
          self.pool = Pool(self.processes_per_search)
          self.multiprocessing = multiprocessing
          self.engine = engine
          self.strategy = strategy

     def __request_url_as_string(self, url):
          return requests.get(url).text

     def summarize(self,pdf_url, should_download=True, max_pages_processed = 20):
          """
          summarize the pdf via URL.
          
          The function first downloads the file, saves it locally and then processes it in parallel (based on the amount of cores available on the machine).

          Input 
          - pdf_url: a url containing the PDF file to summarize.

          Output
          - PDFSummary with the summary information.
          """
          filename = pdf_url
          
          # download the PDF locally so it could be processed later on
          if should_download:
               cont, filename=self.__download_file(pdf_url)
               if not cont:
                    return None
               if filename is None:
                    return PDFSummary()
          
          # call the PDF engine to convert the PDF to a text file
          content=self.engine.get_pdf_content(filename, max_pages_processed, self.pool, self.multiprocessing, self.strategy)
          if should_download:
               self.__safe_delete_file(filename)
          if content is None:
               return PDFSummary()

          # Execute regular expressions on the text to match for expressions (such as abstract, keywords)
          return PDFSummary(
               conclusions = self.__get_text(content,self.CONCLUSION_REGEX),
               keywords=self.__get_text(content,self.KEYWORDS_REGEX),
               summary = self.__get_text(content, self.ABSTRACT_REGEX),
               future_work = self.__get_text(content,self.FUTURE_WORK_REGEX)
               )

     def __safe_delete_file(self,filename):
          try:
               os.remove(filename)
               logging.info(f"The file:{filename} is successfully deleted.")
          except Exception as e:
               logging.error(f"The file:{filename} cannot be deleted. Error: {e}")

     def fetch_urls(self, url, url_fetcher=__request_url_as_string):
          """
          fetch_urls fetches PDF urls based on a given URL.
          
          Input 
          - url:         a url containing the PDF links.
          - url_fetcher: a function responsible for getting the content of the url page.

          Output
          - List containing the PDF URLs.
          """
          try:
               response = url_fetcher(self, url)
               soup = BeautifulSoup(response, 'html.parser')
               list_of_urls = []
               for link in soup.find_all('a', href=True):
                    if ".pdf" in link['href'] and link['href'].startswith("http"):
                         pdf_url=self.__get_url_from_page(link)
                         authors=self.__get_authors_from_page(link)
                         title=self.__get_title_from_page(link)
                         list_of_urls.append((pdf_url,title,authors))
               distinct_url_list= list(set(list_of_urls))
               logging.info("Fetched: {e} urls".format(e=len(distinct_url_list)))
               return distinct_url_list
          except Exception as e:
               logging.error("Error while fetching URLs. Error: {e}".format(e=e))
               return []

     
     def __get_url_from_page(self, link):
          try:
               return link['href']
          except Exception as e:
               logging.error("Error while fetching URL. Error: e".format(e=e))
               return ""

     def __get_authors_from_page(self, link):
          try:
               return link.parent.parent.parent.parent.find_all("div", {"class":"gs_a"})[0].text.split("\xa0")[0]
          except Exception as e:
               logging.error("Error while fetching authors. Error: e".format(e=e))
               return ""

     def __get_title_from_page(self, link):
          try:
               return link.parent.parent.parent.parent.find_all("h3", {"class":"gs_rt"})[0].find_all("a")[0].text
          except Exception as e:
               logging.error("Error while fetching title. Error: e".format(e=e))
               return ""

     def __get_text(self, text,regex_flags_pairs):
          for regex, flags in regex_flags_pairs:
               res = re.search(regex, text, flags)
               if res is not None and len(res.groups()) > 0:
                    return res.group(1).replace("/\n","\n")
          return self.DEFAULT

     def _get_pdf_content(self,filename, max_pages_processed):
          try:
               pdfFile = open(filename,'rb')
               pages = list(PDFPage.get_pages(pdfFile,pagenos=set(),maxpages=0,password='',caching=True,check_extractable=True))
               index_page_pair = [(index, filename) for index in range(min(len(pages), max_pages_processed))]
               merged_output = StringIO()

               if self.multiprocessing:
                    res = self.pool.starmap(get_pdf_page, index_page_pair)
                    def getKey(item):
                         return item[1]
                    sorted(res, key=getKey)
                    [merged_output.write(part[0].getvalue()) for part in res]

               else:
                    resource_manager = PDFResourceManager(caching=True)
                    laParams = LAParams()
                    text_converter = TextConverter(resource_manager,merged_output,laparams=laParams)
                    interpreter = PDFPageInterpreter(resource_manager,text_converter)
                    for index, filename in index_page_pair:
                         interpreter.process_page(pages[index])
               pdfFile.close()     
               return merged_output.getvalue()
          except Exception as e:
               logging.error("Cannot convert PDF: {filename} into text. Error: {e}".format(filename=filename, e=e))
               return None

     def __download_file(self,download_url,filename="tmp_{epoch}.pdf".format(epoch=str(int(float(datetime.now().timestamp()))))):
          try:
               if not str(download_url).lower().strip().startswith("http"):
                    return (False, None)
               response = urllib.request.urlopen(download_url)
               file = open(filename, 'wb')
               file.write(response.read())
               file.close()
               return (True, filename)
          except HTTPError as http_error:
               logging.error("HTTP Error downloading the file {filename} from url {url}. Error : {e}"\
                    .format(e = http_error, filename = filename, url = download_url))
               if http_error.code == "404":
                    return (False,None)
               return (True,None)
          except Exception as e:
               logging.error("Error downloading the file {filename} from url {url}. Error : {e}"\
                    .format(e = e, filename = filename, url = download_url))
               return (True, None) 

     def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict

     def __setstate__(self, state):
        self.__dict__.update(state)

class PDFSummary:
     """
     PDFSummary is a DTO (Data Transfer Object) containing information about the content of the PDF.
     """     
     NOT_APPLICABLE ="N/A"

     def __init__(self, keywords=NOT_APPLICABLE, summary=NOT_APPLICABLE, future_work=NOT_APPLICABLE, conclusions=NOT_APPLICABLE):
        self.keywords = keywords
        self.summary = summary
        self.future_work = future_work 
        self.conclusions = conclusions

     def __eq__(self, __o: object) -> bool:
         if isinstance(__o, PDFSummary):
              return self.keywords == __o.keywords and self.summary == __o.summary and \
                   self.future_work == __o.future_work and self.conclusions == __o.conclusions
         return False

def get_pdf_page(index, filename):
     logging.info("processing page {index} of file {filename}".format(index=index,filename=filename))
     pdfFile = open(filename,'rb')
     pages = list(PDFPage.get_pages(pdfFile,pagenos=set(),maxpages=0,password='',caching=True,check_extractable=True))
     resource_manager = PDFResourceManager(caching=True)
     output_text = StringIO()
     laParams = LAParams()
     text_converter = TextConverter(resource_manager,output_text,laparams=laParams)
     interpreter = PDFPageInterpreter(resource_manager,text_converter)
     interpreter.process_page(pages[index])
     pdfFile.close()
     return output_text, index

def get_pdf2_page(index, filename):
     logging.info("processing page {index} of file {filename}".format(index=index,filename=filename))
     pdfFileObj = open(filename,'rb')
     pdfFile = PdfFileReader(pdfFileObj)
     output_text = pdfFile.getPage(index).extractText()
     pdfFileObj.close()
     return output_text, index

def get_pymupdf_page(index, filename):
     logging.info("processing page {index} of file {filename}".format(index=index,filename=filename))
     pages = fitz.open(filename)
     text = pages[index].get_text("text")
     return text