'''
Takes a patient record and generates a query.
'''
import logging
import argparse
import re
import requests

from collections import OrderedDict
from utils import get_queries
from utils import SPECIAL_MEDICAL_TERMS

logger = logging.getLogger('matcher')


def only_keep_medical_concepts(text: str, quick_umls_service):
    url = 'http://{}/match'.format(quick_umls_service)
    payload = {"text": text}
    try:
        response = requests.post(url, json=payload)
        concepts = response.json()
        ngrams = [con['ngram'] for con in concepts]
        return " ".join(list(OrderedDict.fromkeys(ngrams)))
    except Exception as e:
        logging.error("Unable to connect to the QuickUMLS mapping service at", url)
        raise


def flip_gender(gender):
    if gender == 'Male':
        return 'Female'
    elif gender == 'Female':
        return 'Male'
    else:
        return "Unknown"


def parse_demographics(query_str):
    '''
    Extract age and gender from the query.
    '''

    # try get age in years
    age = [float(x) for x in re.findall('([0-9]+)-year-old', query_str)]

    # no age in year - try in months
    if not age:
        age = [float(x) / 12 for x in re.findall('([0-9]+)-month-old', query_str)]
    age = age.pop() if len(age) > 0 else 0.0

    gender = "Unknown"
    if re.search("female|woman|girl|lady", query_str):
        gender = "Female"
    elif re.search("male|man|boy|gentleman", query_str):
        gender = "Male"

    return {"age": float(age), "gender": gender}


def generate_query(text,
                   country='',
                   custom_filters={},
                   num_results=10,
                   strip_punc=True,
                   keep_umls=True,
                   demographics_filtering=True,
                   only_recruiting=False,
                   quick_umls_service='plexa-quickumls-rest:5000'):
    query_str = text

    special_terms = [st for st in SPECIAL_MEDICAL_TERMS if st.lower() in text.lower()]

    if strip_punc:
        query_str = re.sub('[^0-9a-zA-Z]+', ' ', text)

    if keep_umls and quick_umls_service:
        query_str = only_keep_medical_concepts(query_str, quick_umls_service)

    if demographics_filtering:
        demographics = parse_demographics(text)
        age = demographics['age']  # age == 00 -> no age defined
        gender = demographics['gender']

    query_str = query_str + " " + " ".join(special_terms)

    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": query_str.strip()
                        }
                    }
                ]
            }
        },
        "from": 0,
        "size": str(num_results),
        "aggs": {
            "gender_agg": {
                "terms": {"field": "clinical_study.eligibility.gender"}
            },
            "eligibility.Treatment_agg": {
                "terms": {"field": "clinical_study.eligibility.Treatment"}
            },
            "status": {
                "terms": {"field": "clinical_study.overall_status"}
            }
        }
    }

    for (key, value) in custom_filters.items():
        value = value.lower() if type(value) == str else value
        custom_filter = {"match_phrase": {"clinical_study." + key: value.lower()}}
        query['query']['bool']['must'].append(custom_filter)

    if country:
        country_filter = {
            "match_phrase": {"clinical_study.location_countries.country": country.lower()}
        }
        query['query']['bool']['must'].append(country_filter)

    if only_recruiting:
        only_recruiting_filter = {
            "term": {"clinical_study.overall_status": "Recruiting"}
        }
        query['query']['bool']['must'].append(only_recruiting_filter)

    if demographics_filtering:
        demographics_filter = {
            "bool": {}
        }

        gender_filter = {
            "term": {"clinical_study.eligibility.gender": flip_gender(gender)}
        }
        demographics_filter['bool']['must_not'] = gender_filter

        if age > 0.0:
            age_filter = [
                {
                    "range": {
                        "clinical_study.eligibility.minimum_age": {
                            "lte": age
                        }
                    }
                },
                {
                    "range": {
                        "clinical_study.eligibility.maximum_age": {
                            "gte": age
                        }
                    }
                }
            ]
            demographics_filter['bool']['must'] = age_filter

        query['query']['bool']['must'].append(demographics_filter)

    return query


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert patient record to clinical query.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-q', '--query_file', help='Query file in Indri format.')
    parser.add_argument('query_keywords', nargs='?')
    args = parser.parse_args()

    if args.query_file:
        queries = get_queries(args.query_file)
        for qid, keywords in queries.items():
            print('{}:\t{}'.format(qid, generate_query(keywords)))
    elif args.query_keywords:
        print(generate_query(args.query_keywords, quick_umls_service='localhost:5000'))
    else:
        parser.print_usage()
