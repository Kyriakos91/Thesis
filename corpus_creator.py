from scrapper import Domain, Field 
import yaml
import os.path

class CorpusCreator:
    """
    CorpusCreator is a class that is responsible for creating a corpus for the engines to load, based on provided fields. 

    Currently the corpus only supports yml files.
    """
    CORPUS_EXTENTION = ".yml"
    DOMAIN_MATCH_PREFIX = 'This is the hierarchy I found: '
    DOMAIN_MATCH_SEPARATOR = " > "
    DOMAIN_SEPARATOR = " / "
    DOMAIN_PREFIX = 'Here are the following sub-domains: '
    FIELD_QUESTIONS=[
        'what are the fields?',
        'what are the available fields?',
        'what fields are available?',
        'fields', 'field',
    ]
    GREETING_QUESTIONS=[
        'hi','hello','hey','help'
    ]
    GREETING_MESSAGE='Hello. I am OAR and im here to help you with creating a list of articles \
    of your field based on our conversation. Please select one of the following fields: '

    def __init__(self, corpus_location, corpus_flush = None) -> None:
        """
        Creating of the CorpusCreator class.

        Configuration 
        - corpus_location:  where to flush corpus files.
        - corpus_flush:     function that implements how to flush the files into a file. The default one is YML. 
        """
        self.corpus_location = corpus_location
        if corpus_flush == None:
            self.corpus_flush = self._create_yaml_file
        else:
            self.corpus_flush = corpus_flush
    
    def create(self, fields) -> None:
        """
        create creates the corpuses - yml files.

        Input 
        - fields: fields to create corpus from.
        """
        field_names=[]
        for field in fields:
            dictionary = self._convert_to_dictionary(field)
            self.corpus_flush(field.name, dictionary)
            field_names.append(field.name)
        list_of_fields=self.DOMAIN_SEPARATOR.join(x for x in field_names)    
        self.__generate_questions__(self.FIELD_QUESTIONS,list_of_fields,'fields')
        self.__generate_questions__(self.GREETING_QUESTIONS,self.GREETING_MESSAGE + list_of_fields,'greetings')

    def __generate_questions__(self,questions,answer,category) -> None:
        conversations=[]
        for question in questions:
            conversations.append([question, answer])
        self.corpus_flush(category, conversations)

    def _create_yaml_file(self, name, content) -> None:
        dict_file = {'categories':[name], 'conversations':content}
        full_path = os.path.join(self.corpus_location, name + self.CORPUS_EXTENTION)
        with open(full_path, 'w') as file:
            yaml.dump(dict_file, file, default_flow_style=False)

    def _convert_to_dictionary(self, field:Field):
        conversations = []
        def _convert_from_domain(domain:Domain, hierarchy = []):
            if not domain.subdomains:
                hierarchy.append(domain.name)
                conversations.append([domain.name, self.__generate_domain_answer(hierarchy)])
                return
        
            conversations.append([domain.name, self.__generate_domain_response(domain.subdomains)])

            for subdomain in domain.subdomains:
                _convert_from_domain(subdomain, hierarchy + [domain.name])

        if not field.domains:
            conversations.append([field.name, self.__generate_domain_answer([field.name])])
        else:
            conversations.append([field.name, self.__generate_domain_response(field.domains)])
            for domain in field.domains:
                _convert_from_domain(domain, [field.name])
        return conversations

    def __generate_domain_answer(self, domains):
        return self.__clean_answer('{prefix}{answer}'.format(
            prefix = self.DOMAIN_MATCH_PREFIX,
            answer = self.DOMAIN_MATCH_SEPARATOR.join(x for x in domains)
        ))
    
    def __generate_domain_response(self, domains):
        return self.__clean_answer('{prefix}{answer}'.format(
            prefix = self.DOMAIN_PREFIX,
            answer = self.DOMAIN_SEPARATOR.join(x.name for x in domains)
        ))

    def __clean_answer(self,line):
        return line.replace("\'", "").strip().replace("\"", "")