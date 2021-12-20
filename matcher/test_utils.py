import unittest
import utils

from collections import defaultdict

class MatchTest(unittest.TestCase):
    
    def test_get_rankings(self):
        rankings: defaultdict = utils.get_rankings('results/topics-trecds-all.txt.res')
        self.assertTrue(len(rankings)>0)
                
        first_query, first_query_results = rankings.popitem()
        first_doc = first_query_results[0]
        self.assertEqual(4, len(first_doc))
        doc, rank, score, comment = first_doc
        self.assertEqual(1, rank)
        self.assertTrue(score > 0.0)
        
if __name__ == '__main__':
    unittest.main()