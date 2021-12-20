"""
Unit tests for trial_parser.py
"""
import unittest
from trial_parser import TrialParser

class TestTrailParser(unittest.TestCase):


    def test_split_criteria(self):
        crit = '''Inclusion Criteria:
            -  Thoracic surgical patients requiring lung isolation
            -  Pulmonary resection: lobectomy, segmentectomy
            -  Esophageal surgery and no pulmonary resection
            -  Mediastinal surgery and no pulmonary resection

            Exclusion Criteria:
            -  Metabolic disorder
            -  Metabolic syndrome
            -  Diabetes
            -  Pregnancy'''
            
        inclusion, exclusion = TrialParser().split_inclusion_and_exclusion(crit)
        self.assertNotEqual(inclusion, exclusion)
        self.assertEqual(inclusion[0:19], 'Inclusion Criteria:')
        self.assertEqual(exclusion[0:19], 'Exclusion Criteria:')
        
    def test_extract_criteriob(self):
        crit = '''Inclusion Criteria:
            -  Thoracic surgical patients requiring lung isolation
            -  Pulmonary resection: lobectomy, segmentectomy
            -  Esophageal surgery and no pulmonary resection
            -  Mediastinal surgery and no pulmonary resection'''
            
        criteria = TrialParser().extract_criterion(crit)
        
        for c in criteria:
            print(c)
        
        self.assertEqual(5, len(criteria))
        
    
    def disabled_test_spacy_parse(self):
        '''
        Test class stubs for using Spacy - NotImplemented
        '''
        results = TrialParserSpacy().parse("Must have a clinical diagnosis of Alzheimer's Disease.")
        for chunk in results.noun_chunks:
            print("--")
            print("chunk.text", chunk.text)
            print("chunk.root.text", chunk.root.text)
            print("chunk.root.dep_", chunk.root.dep_)
            print("chunk.root.head.text", chunk.root.head.text)
        self.assertAlmostEqual("hello", "hi")
    
    def disabled_test_role_labelling(self):
        '''
        Test class stubs for using AllenAI - NotImplemented
        '''
        roles = TrialParserAllenAI().get_roles(sentence="Subjects with a past or current history of seizures cannot participate but can observe from afar..")
        print(roles)
        for role in roles:
            print(role)
            print('--')
        self.assertEqual("Foo", "Foo")
        
if __name__ == '__main__':
    unittest.main()