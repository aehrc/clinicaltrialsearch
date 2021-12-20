import unittest
import query_generation

from collections import defaultdict
from utils import get_queries


class QueryGenerationTest(unittest.TestCase):

    def test_parse_demographic(self):
        demographics = query_generation.parse_demographics("A 58-year-old African-American woman presents to the ER.")
        self.assertEqual(58, demographics['age'])
        self.assertEqual("Female", demographics['gender'])

    def test_parse_demographic_all(self):
        queries = get_queries('test_collection/topics-treccds-all.txt')
        for qid, keywords in queries.items():

            demographics = query_generation.parse_demographics(keywords)
            print(qid, demographics)
            self.assertGreaterEqual(demographics['age'], 0)
            self.assertTrue(demographics['gender'] in ["Male", "Female", "Unknown"])
            if demographics['gender'] == "Unknown":
                print(keywords)

    @staticmethod
    def test_generate_query():
        query_generation.generate_query("lung", quick_umls_service="localhost:5000")


if __name__ == '__main__':
    unittest.main()
