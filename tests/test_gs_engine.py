from db import MockDB
from engines.engine import GoogleScholarQueryEngine
import unittest

class TestGoogleScholarEngine(unittest.TestCase):
    def test_compose_url(self):
        engine = GoogleScholarQueryEngine(MockDB())
        gs_url = engine._compose_gs_url(["M","K"], ["ba","Am","M"])
        self.assertEquals(gs_url,engine.GS_URL+"M+Ks+ba+Am+M")

if __name__ == '__main__':
    unittest.main()

