from typing import List
import wikipedia
from bs4 import BeautifulSoup
import requests

class Domain:
    """
    Domain is a class that encapsulates a domain and a list of sub-domains.
    """
    def __init__(self, name, subdomains=None):
        self.name=name.lower()
        if subdomains is None:
            self.subdomains = []
        else: 
            self.subdomains = subdomains

    def add_subdomain(self, domain):
        self.subdomains.append(domain)

    def add_subdomain_by_str(self, str_domain):
        self.add_subdomain(Domain(name=str_domain))

    def merge_subdomains(self, subdomains):
        for subdomain in subdomains:
            if not self.subdomains.__contains__(subdomain):
                self.subdomains.append(subdomain)

    def __eq__(self, __o: object) -> bool:
        return self.name == __o.name

class Field:
    """
    Field is a class that encapsulates a field and a list of domains.
    """
    def __init__(self, name, domains:List[Domain]=None):
        self.name=name.lower()
        if domains is None:
            self.domains = []
        else: 
            self.domains = domains

    def get_domain(self,domain_name):
        d = []
        def _get_subdomains(domains, domain_name,d):
            for domain in domains:
                if domain.name==domain_name:
                    d.append(domain)
                if len(domain.subdomains)>0:
                    _get_subdomains(domain.subdomains,domain_name, d)
            
        _get_subdomains(self.domains,domain_name, d)
        return d

class FieldScrapper:
    """
    FieldScrapper is a class responsible to scrape for new domains.
    """
    def scrape(self):
        """
        scrape scrapes fields from Wikipedia while parses them in a proper hierarchy. This class is tailored 
        only for Wikipedia and likely to break if Wikipedia will change their layout. 
       
        Output 
        - List of Field objects.
        """
        wiki_fields=wikipedia.page('List_of_academic_fields').content
        #remove the unnecessary text
        wiki_fields = wiki_fields[wiki_fields.rfind("== Humanities and social science =="):wiki_fields.rfind("== See also ==")]

        #remove lines 
        lines = wiki_fields.split("\n")
        non_empty_lines = [line for line in lines if (line.strip() != "")]
        clean_wiki_fields = ""

        for line in non_empty_lines:
            if line[0]=="=":
                clean_wiki_fields += line + "\n" 

        #cleaning fields
        clean_wiki_fields=clean_wiki_fields.split("\n")
        clean_wiki_fields = [line for line in clean_wiki_fields if (line.strip() != "")]
        fields=self.__creating_fields(clean_wiki_fields,0)

        #scraping more domains for each field using beautifulSoup
        url="https://en.wikipedia.org/wiki/List_of_academic_fields"
        response=requests.get(url)
        soup=BeautifulSoup(response.text, 'html.parser')
        
        #targeting the specific headlines of the web page
        heading_tags = ["h3", "h4", "h5"] 
        parent = Field("p")
        for link in soup.find_all(heading_tags):
            if link.get_text().split('[')[0]=="\nPersonal tools\n":
                break
            d  = Domain(name=link.get_text().split('[')[0])
            parent.domains.append(d)
            for sib in link.findNextSiblings('div'):
                if "<div>" in str(sib):
                    for col in sib.findChildren("td"):
                            self.__domain_scraping(col, d)
                    break
                elif sib.get("class")[0]=="div-col":
                    self.__domain_scraping(sib, d)
                    break

        #Appending the new subdomains to the existing fields and domains                
        for field in fields:
            for domain in field.domains:
                for subdomain in domain.subdomains:
                    d2 = parent.get_domain(subdomain.name)
                    if len(d2) > 0:
                        subdomain.merge_subdomains(d2[0].subdomains)
                d = parent.get_domain(domain.name)
                if len(d) > 0:
                    domain.merge_subdomains(d[0].subdomains)
        return fields

    def __get_domain_name(self,f):
     link =  f.find('a', recursive=False)
     if link is None:
          return f.get_text().replace("\n","")
     else:
          return  link.get_text()

    def __domain_scraping(self,col, domain:Domain):
        for li in col.findChild("ul").findChildren("li", recursive=False):
            if "<ul" in str(li):
                child_domain = Domain(name=self.__get_domain_name(li))
                for li_ in li.findChild("ul").findChildren("li", recursive=False):
                        if "<ul" in str(li_):
                            child_child_domain = Domain(name=self.__get_domain_name(li_))
                            for li__ in li_.findChild("ul").findChildren("li", recursive=False):
                                child_child_domain.add_subdomain_by_str(self.__get_domain_name(li__))
                            child_domain.add_subdomain(child_child_domain)
                        else:
                            child_domain.add_subdomain_by_str(self.__get_domain_name(li_))
                domain.add_subdomain(child_domain)
            else:
                domain.add_subdomain_by_str(self.__get_domain_name(li))

    def __creating_fields(self,clean_wiki_fields,index)-> List[Field]:
        fields=[]
        for line in clean_wiki_fields:
            if line.startswith("== "):
                fields.append(Field(name=self.__clean_line(line)))
                index=index+1
            else:
                self.__creating_domains(line,fields[index-1])
            
        return fields

    def __creating_domains(self,line:str,last_field:Field):
        if line.startswith("=== "):
            last_field.domains.append(Domain(name=self.__clean_line(line)))

        if line.startswith("==== "):
            last_field.domains[len(last_field.domains) -1].subdomains.append(Domain(name=self.__clean_line(line)))

        if line.startswith("===== "):
            last_field.domains[len(last_field.domains) -1].subdomains[len(last_field.domains[len(last_field.domains) -1].subdomains) -1].subdomains.append(Domain(name=self.__clean_line(line)))

    def __clean_line(self,line):
        return line.replace("=", "").strip()
