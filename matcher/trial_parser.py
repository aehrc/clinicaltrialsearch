import argparse
import glob

import xml.etree.ElementTree

from typing import List, Dict
from tqdm import tqdm

class TrialParser:
    
    def __init__(self):
        #import spacy
        #self.nlp = spacy.load("en_core_web_sm")
        pass
    
    def get_eligibity_block():
        pass
    
    def process_file(self, filename):
        try:
            root = xml.etree.ElementTree.parse(filename)
        except xml.etree.ElementTree.ParseError:
            print('Error parsing {}'.format(filename))
            raise
        for elem in root.findall('.//eligibility/criteria/textblock'):   
            inclusion, exclusion = self.split_inclusion_and_exclusion(elem.text)
            for (extention,content) in zip(('inclusion', 'exclusion'), (inclusion, exclusion)):
                with open('{}.{}'.format(filename, extention), 'w') as fh:
                    for crit in self.parse_eligibility(content):
                        fh.write(crit+'\n')
    
    def split_inclusion_and_exclusion(self, eligibility_block):
        inclusion = eligibility_block
        exclusion = ''
        begin_exclusion = eligibility_block.lower().find('exclusion')
        if begin_exclusion:
            inclusion = eligibility_block[:begin_exclusion]
            exclusion = eligibility_block[begin_exclusion:]
        return (inclusion, exclusion)
    
    def parse_eligibility(self, text):
        crit = ''
        crits = []
        for line in text.split('\n'):
            if len(line.strip()) == 0:
                crits.append(crit)
                crit = ''
            crit = crit + ' ' +line.strip()
        crits.append(crit)
        
        return crits

    def extract_criterion(self, criteria):
        #criteria = criteria.replace('\n', '.\n')
        # tokens = self.nlp(criteria)
        return criteria.split('\n')

class TrialParserSpacy:
    

    def __init__(self):
        import spacy
        self.nlp = spacy.load("en_core_web_sm")
        
    def parse(self, text):
        tokens = self.nlp(text)
        return doc


        
if __name__ =='__main__':
    parser = argparse.ArgumentParser(description="Parse trials")
    parser.add_argument('-d', '--directory', help="Directory of files to process")
    parser.add_argument('-f', '--file', help="File process")
    
    args = parser.parse_args()
    
    if args.directory:
        for f in tqdm(glob.glob(args.directory+'/*.xml')):
            TrialParser().process_file(f)
    elif args.file:
        TrialParser().process_file(args.file)
    else:
        parser.print_help()