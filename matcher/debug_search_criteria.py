from matcher import search
from trial_parser import TrialParser

for result in search('malaria', num_results = 1000, elastic_service='localhost:9200', quick_umls_service=None):
    crit = result['eligibility']['criteria']
    
    
    for pos in crit['inclusion'].split("\n"):
        print('+', pos)
        
    
    for neg in crit.get('exclusion', "").split("\n"):
        print('^', neg)
        
    print('*'* 100)