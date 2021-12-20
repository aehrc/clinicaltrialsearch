
import xml.etree.ElementTree as etree
import re
import argparse

from typing import Dict, Union, Optional, List, Any

from collections import defaultdict


SPECIAL_MEDICAL_TERMS = ['covid', 'covid-19', 'coronavirus', 'corona']

def get_queries(query_file: str):
    """ 
    Reads a Indri formatted query file.
    :param query_file: An Indri formatted query file.
    :return A dict of queryId -> queryTxt
    """
    with open(query_file, 'r') as xml_file:
        tree = etree.parse(xml_file)
        queries = dict([ (query.findtext('number'), query.findtext('text')) for query in tree.getroot()])
    return queries

def trec_pm_to_indri(query_file: str) -> Dict[str, str]:
    """
    Takes a file in TREC PM format and converts to Dict[query_id -> query string]
    """
    topic_year:str = re.findall('[0-9]{4}', query_file)[0] if re.findall('[0-9]{4}', query_file) else ''
    queries: Dict[str, str] = {}
    with open(query_file, 'r') as xml_file:
        tree: etree.ElementTree = etree.parse(xml_file)
        
        for query in tree.findall('topic'): #type: etree.Element
            # query: etree.Element = query
            qId = topic_year + query.attrib['number']
            query_text: str = '. '.join([i.text for i in query.iter() if i.text.strip() and i.text.strip() != 'None'])
            queries[qId] = query_text
        return queries

def get_rankings(ranking_file: str):
    """
    Reads a TREC style ranking file and returns as dict.
    :param ranking_file: TREC style ranking file.
    :return Dict of queryId -> [d_0, ..., d_n]
    """
    # rankings: Dict[str, Optional[List[Any]]] = {}
    rankings = defaultdict(list)
    with open(ranking_file) as fh:
        for line in fh:
            qid, zero, doc, rank, score, runId = line.strip().split()
            rankings[qid].append((doc, int(rank), float(score), runId))
    return rankings

def format_trec_results(qid: str, doc: str, rank: int, score: float, run_id='RunId'):
    """
    Produce a TREC formatted str of results.
    :param qid: Query Id
    :param doc: Document
    :param rank: Rank position
    :param score: Ranking score
    :param run_id: Name for this run
    :return String in TREC format
    """
    return '{}\t0\t{}\t{}\t{:.4f}\t{}'.format(qid, doc, rank, float(score), run_id)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Helper utils for matcher.')
    parser.add_argument('-q', '--query_file', help='Print queries.')
    parser.add_argument('-t', '--trec_pm', help='Convert TREC PM to Indri format for matcher.')
    args = parser.parse_args()
    
    if args.query_file:
        for qId, text in get_queries(args.query_file).items():
            print('{}: {}'.format(qId, text))
    elif args.trec_pm:
        print('<queries>')
        for qid, query_txt in trec_pm_to_indri(args.trec_pm).items():
            print('<query>')
            print('<number>{}</number>'.format(qid))
            print('<text>{}</text>'.format(query_txt))
            print('</query>')
        print('</queries>')