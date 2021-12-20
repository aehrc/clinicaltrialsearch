import argparse
import logging
import json
from tqdm import tqdm
from elasticsearch import Elasticsearch


INDEX_NAME = 'clinicaltrials'


def index():
    es = Elasticsearch()
    es.bulk()


def index_one(json_file, elastic_service='http://localhost:9200'):

    es = Elasticsearch()

    with open(json_file) as fh:

        document = json.load(fh)
        passed = list(document['clinical_study'].keys())
        broken = []

        for field_key in passed:
            trimmed_doc = document

            del trimmed_doc['clinical_study'][field_key]
            try:
                res = es.index(index=INDEX_NAME, doc_type='trials', body=json.dumps(trimmed_doc, sort_keys=True, indent=4))
                index_doc_count = 0
                if res['result'] == 'created':
                    index_doc_count = index_doc_count + 1
                else:
                    print(f"Error on {field_key}")
                    raise Exception("Unable to index: {}".format(res))
                print(f"{field_key}: pass")
            except:
                raise
                broken = broken + [field_key]
                print(f"{field_key}: fail")

        print(f"{json_file}: {len(broken)} broken / {len(passed)}")


def read_one(json_file):
    with open(json_file) as fh:
        for line in fh:
            if not line.startswith('{ "index"'):
                if 'clinical_results' in line:
                    json_doc = json.loads(line)
                    phone = json_doc['clinical_study']['clinical_results']['point_of_contact']['phone']
                    print(phone)




if __name__ == '__main__':
    files = ['../indexer/json_out/clinical_trials-0.json', '../indexer/json_out/clinical_trials-x.json']
    read_one('../indexer/json_out/clinical_trials-0.json')
    # for f in files:
    #     index_one(f)
