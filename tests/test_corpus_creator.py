from corpus_creator import CorpusCreator
from scrapper import Domain, Field 
import unittest

class TestCorpusCreator(unittest.TestCase):
    def test_yaml_creation(self):
        parsed_fields = {}

        def _create_local(name, content):
            parsed_fields[name] = content
            
        # Arrange
        fields = [\
            Field(
                name="Computer Science",
                domains=[
                    Domain(name="Machine Learning", \
                        subdomains=[\
                            Domain(name="Supervised"), 
                            Domain(name="Unsupervised"), 
                            Domain(name="Reinforcement Learning")])])
            , Field(
                name="Databases",
                domains=[
                    Domain(name="Relational")])
            , Field(
                name="Orphan",
                domains=[])]

        scrapper = CorpusCreator("./", _create_local)
         
        # Act
        scrapper.create(fields)
        
        # Assert
        expected_fields = {
            'Computer Science': [
                ['Computer Science', 'Machine Learning'],
                ['Machine Learning', 'Supervised, Unsupervised, Reinforcement Learning'],
                ['Supervised', 'Computer Science > Machine Learning > Supervised'],
                ['Unsupervised', 'Computer Science > Machine Learning > Unsupervised'],
                ['Reinforcement Learning', 'Computer Science > Machine Learning > Reinforcement Learning'],
            ],
            'Databases': [
                ['Databases', 'Relational'],
                ['Relational', 'Databases > Relational'],
            ],
            'Orphan': [
                ['Orphan', ' > Orphan']
            ]
        }
        self.assertEqual(parsed_fields,expected_fields,"fields should be identical to the dictionary")


if __name__ == '__main__':
    unittest.main()

