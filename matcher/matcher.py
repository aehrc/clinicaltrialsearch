'''
Submit queries to ES.
'''

import os
import json
import sys
import argparse
import logging

from elasticsearch import Elasticsearch, helpers
from utils import get_queries
from query_generation import generate_query

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S')

logger = logging.getLogger('matcher')
logger.setLevel(logging.INFO)


def get_qrels(qrel_file='test_collection/qrels-all.txt'):
    """
    Return qrels in the form qiddoc -> relevance, where qiddoc is qid concat with doc.
    """
    qrels = {}
    if os.path.exists(qrel_file):        
        with open(qrel_file) as fh:
            for line in fh:
                qid, zero, doc, relevance = line.strip().split()
                qrels[qid+doc] = relevance
    return qrels


def search(query, 
           qid='', 
           num_results=10, 
           country='',
           custom_filters={},
           demographics_filtering=True,
           only_recruiting=False,
           elastic_service='plexa-elasticsearch:9200', 
           index='clinicaltrials', 
           quick_umls_service='plexa-quickumls-rest:5000'):
    
    # generate the query
    query_payload = generate_query(query, 
                                   num_results=num_results, 
                                   country=country,
                                   custom_filters=custom_filters,
                                   only_recruiting=only_recruiting, 
                                   demographics_filtering=demographics_filtering, 
                                   quick_umls_service=quick_umls_service)
    
    logger.debug(json.dumps(query_payload, indent='\t'))

    # do the search
    hostname, port = elastic_service.split(':', 1)
    logger.debug('Connect to ES service "{}" on port {}'.format(hostname, port))
    es = Elasticsearch([hostname], port=port)
    results = helpers.scan(es, query=query_payload, index=index, preserve_order=True)

    # if there is no query id then make one from query keywords
    qid = qid if len(qid) > 0 else query.replace(' ', '_')[0:min(8, len(query))]
    
    # get qrels if they exist
    qrels = get_qrels()

    # build up and yield all the results
    count = 0
    for count, hit in enumerate(results):
        if count == num_results:
            break
        result = {
            'qid': qid, \
            'doc': hit['_source']['clinical_study']['id_info']['nct_id'], \
            'rank_pos': count+1, \
            'score': round(hit['_score'],4), 
            'id': hit['_id'], \
            'title': hit['_source']['clinical_study']['brief_title'], \
            'summary': hit['_source']['clinical_study']['brief_summary']['textblock'], \
            'run_id': qrels.get(qid+hit['_source']['clinical_study']['id_info']['nct_id'], "n")} 
        for (attribute, value) in hit['_source']['clinical_study'].items():
            result[attribute] = value
        yield result
    

def print_results(results):
    r = {'qid': '', 'rank_pos': 0}
    for r in results:
        print('{qid}\t0\t{doc}\t{rank_pos}\t{score}\t{run_id}'.format(**r))
    print("Query {qid}: {rank_pos} results".format(**r), file=sys.stderr)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Search Elastic.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-e', '--elastic_service', default='localhost:9200', help='Elastic search endpoint.')
    parser.add_argument('-u', '--quickumls_service', default='localhost:5000', help='QuickUMLS service.')
    parser.add_argument('-n', '--num_results', type=int, default=10, help='Max number of results per query')
    parser.add_argument('-q', '--query_file', help='Query file in Indri format.')
    parser.add_argument('-d', '--disable_demographics_filtering', help='Filter results based on age & gender.', action='store_true', default=False)
    parser.add_argument('-r', '--recruiting_trials_only', help='Return only trials open to recruting.', action='store_true', default=False)
    parser.add_argument('-c', '--country', default='', help='Filter by country.')
    parser.add_argument('-f', '--filters', help='Apply a custom filter in the form field1:value1,field2:value2.')
    parser.add_argument('-v', '--verbose', help='Verbose logging.', action='store_true')
    parser.add_argument('query_keywords', nargs='?')
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.debug("")
        logger.debug("Verbose logging on.")

    filters = {}
    if args.filters:
        for fil in args.filters.split(','):
            f,v = fil.split(':', 2)
            filters[f] = v
        logger.info("Custom filters {}.".format(filters))    
    
    logger.info("Demographics filtering is {}.".format("OFF" if args.disable_demographics_filtering else "ON"))

    if args.query_keywords:
        print_results(
            search( args.query_keywords, 
                    country=args.country, 
                    custom_filters=filters,
                    only_recruiting=args.recruiting_trials_only, 
                    demographics_filtering=not args.disable_demographics_filtering, 
                    num_results=args.num_results, 
                    elastic_service=args.elastic_service, 
                    quick_umls_service=args.quickumls_service)
        )
    elif args.query_file:
        queries = get_queries(args.query_file)
        for qid, keywords in queries.items():
            print_results(
                search( args.query_keywords, 
                        country=args.country,  
                        custom_filters=filters,
                        only_recruiting=args.recruiting_trials_only, 
                        demographics_filtering=not args.disable_demographics_filtering, 
                        num_results=args.num_results, 
                        elastic_service=args.elastic_service, 
                        quick_umls_service=args.quickumls_service)
            )
    
    else:
        parser.print_usage()

