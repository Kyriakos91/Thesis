from pdf import PDF, PDFReadStrategyPortion, PDFSummary,PDFReadStrategyAll
import unittest
import json

class TestPDF(unittest.TestCase):
    def __fetch_local_file(self,_):
        with open("./tests/html_articles_only.html", "r",encoding="utf8") as a_file:
            html_Gs = a_file.read()
        return html_Gs

    def test_fetch_pdfs(self):
        pdf = PDF()
        urls = pdf.fetch_urls("", url_fetcher=self.__fetch_local_file)
        urls.sort()
        expected = [('http://acikerisimarsiv.selcuk.edu.tr:8080/xmlui/bitstream/handle/123456789/14407/519636.pdf?sequence=1&isAllowed=y', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('http://acikerisimarsiv.selcuk.edu.tr:8080/xmlui/bitstream/handle/123456789/14407/519636.pdf?sequence=1&isAllowed=y', 'Decision support system for a football team management by using machine learning techniques', 'MAM Al-Asadi'), ('https://www.scitepress.org/papers/2016/58776/58776.pdf', 'Recognizing compound events in spatio-temporal football data', 'K Richly, M Bothe, T Rohloff…'), ('https://dtai-static.cs.kuleuven.be/events/MLSA13/papers/mlsa13_submission_4.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://www.academia.edu/download/38928979/Using_Machine_Learning_to_Predict_Winners_of_Football_League_for_Bookies.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://www.imperial.ac.uk/media/imperial-college/faculty-of-engineering/computing/public/1718-ug-projects/Corentin-Herbinet-Using-Machine-Learning-techniques-to-predict-the-outcome-of-profressional-football-matches.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://www.academia.edu/download/47098202/D017332126.pdf', 'Support vector machine–based prediction system for a football match result', 'CP Igiri'), ('https://www.academia.edu/download/56704483/1520497925_08-03-2018.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://www.scitepress.org/papers/2016/58776/58776.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://www.academia.edu/download/64023099/45%2015apr19%2013apr19%207des18%2017022__EditAmir.pdf', 'Comparing machine learning and ensemble learning in the field of football', 'S Khan, VB Kirubanand'), ('https://www.academia.edu/download/38920512/tkde-version_1.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://www.academia.edu/download/38928979/Using_Machine_Learning_to_Predict_Winners_of_Football_League_for_Bookies.pdf', 'Using machine learning to predict winners of football league for bookies', 'EO Esumeh'), ('https://dtai-static.cs.kuleuven.be/events/MLSA13/papers/mlsa13_submission_4.pdf', 'Comparison of Machine Learning Methods for Predicting the Recovery Time of Professional Football Players After an Undiagnosed Injury.', 'S Kampakis'), ('https://www.academia.edu/download/64023099/45%2015apr19%2013apr19%207des18%2017022__EditAmir.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://www.academia.edu/download/56704483/1520497925_08-03-2018.pdf', 'Prediction of football match score and decision making process', 'LK Teli, N Zaveri, P Shinde'), ('https://www.academia.edu/download/47098202/D017332126.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://cs229.stanford.edu/proj2015/111_report.pdf', 'Predicting the Dutch football competition using public data: A machine learning approach', 'N Tax, Y Joustra'), ('https://www.imperial.ac.uk/media/imperial-college/faculty-of-engineering/computing/public/1718-ug-projects/Corentin-Herbinet-Using-Machine-Learning-techniques-to-predict-the-outcome-of-profressional-football-matches.pdf', 'Predicting football results using machine learning techniques', 'C Herbinet'), ('https://cs229.stanford.edu/proj2015/111_report.pdf', 'Machine learning for daily fantasy football quarterback selection', 'P Dolan, H Karaouni, A Powell')]
        expected.sort()
        self.assertEquals(urls, expected)

    def ignore_download(self, url):
        return (True, url)

    def test_pdf_summarize(self):
        strategy = PDFReadStrategyAll()
        pdf = PDF()
        fixtures= open("./tests/resources/fixture.json", encoding="utf-8")
        data = json.load(fixtures)
        flush_to_text_file = bool(data["flush_to_text_file"])

        for fixture in data["fixtures"]:
            if (flush_to_text_file) and bool(fixture["active"]):
                txt_file=pdf.engine.get_pdf_content(fixture["filename"],100,pdf.pool, False, strategy=strategy)
                file = open(fixture["filename"]+".txt", 'w',encoding='utf-8')
                file.write(txt_file)
                file.close()

            if not bool(fixture["active"]):
                continue
            
            summarized_pdf = pdf.summarize(fixture["filename"], should_download=False)
            expect_result = PDFSummary(
                summary=fixture["expected_summary"],
                future_work=fixture["expected_future_work"],
                conclusions=fixture["expected_conclusions"],
                keywords=fixture["expected_keywords"])
            # self.assertEquals(summarized_pdf.conclusions, expect_result.conclusions)
            # self.assertEquals(summarized_pdf.future_work, expect_result.future_work)
            # self.assertEquals(summarized_pdf.summary, expect_result.summary)
            # self.assertEquals(summarized_pdf.keywords, expect_result.keywords)

            
            
if __name__ == '__main__':
    unittest.main()