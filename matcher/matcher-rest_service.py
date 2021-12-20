#!/usr/bin/env python

'''
REST service for clinical trials search.

'''

import argparse
import logging
from flask import Flask, request, Response, json, render_template
from flask_httpauth import HTTPBasicAuth

import matcher

__author__ = "koo01a"
__copyright__ = "Copyright 2018, CSIRO"
__created__ = "28/6/18"

logging.basicConfig()
logger = logging.getLogger('matcher')
logger.setLevel(logging.INFO)

app = Flask(__name__)
auth = HTTPBasicAuth()
users = {
    "bevan": "rabbit",
    "plexa": "jhhADfbn$8383c"
}


@auth.get_password
def get_pw(username):
    return users.get(username, None)


quick_umls_service = 'plexa-quickumls-rest:5000'
elastic_service = 'plexa-elasticsearch:9200'


@app.route('/', methods=['GET'])
@auth.login_required
def index():
    return render_template('index.html', version="0.1-2020CT", es_service=elastic_service, q_service=quick_umls_service)


@app.route('/patient', methods=['GET'])
@auth.login_required
def patients():
    with open('patients.json') as json_file:
        patients = json.load(json_file)
        return Response(json.dumps(patients, sort_keys=False, indent="\t"), status=200, mimetype='application/json')


@app.route('/patient/<patient_id>', methods=['GET'])
@auth.login_required
def patient(patient_id):
    with open('patients.json') as json_file:
        patients = json.load(json_file)
        for patient in patients['patients']:
            if patient['patient_id'] == patient_id:
                return Response(json.dumps(patient, sort_keys=False, indent="\t"), status=200,
                                mimetype='application/json')
    return "Unknown patient with id {}.".format(patient_id), 404


@app.route('/', methods=['POST'])
@auth.login_required
def search_endpoint():
    content = request.get_json(silent=True)
    logger.debug(content)

    if not content:
        return "Invalid request - missing content", 400

    if 'query' not in content or len(content['query']) == 0:
        return "Invalid or missing 'query' field.", 400

    custom_filters = {k: v for k, v in content.items() if
                      k not in ['query', 'country', 'num_results', 'recruiting_only']}

    logger.debug("Searching for {}.".format(content['query']))

    try:
        results = [
            r for r in matcher.search(
                content['query'],
                elastic_service=elastic_service,
                custom_filters=custom_filters,
                quick_umls_service=quick_umls_service,
                num_results=content.get('num_results', 10),
                only_recruiting=content.get('recruiting_only', False),
                country=content.get('country', '')
            )
        ]

        logger.debug("Got {} results".format(len(results)))

        return Response(json.dumps(results, sort_keys=False, indent="\t"), status=200, mimetype='application/json')
    except Exception as e:
        # return "Unable to process search " + str(e), 500
        raise e


def wsgi_main():
    return app


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description="Webservice for clinical trials service.",
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('-p', '--port', type=int, default=8888, help="HTTP port for the REST service.")
    argparser.add_argument('-v', '--verbose', action='store_true', help="Turn on verbose logging.")
    argparser.add_argument('-e', '--elastic_service', default='localhost:9200', help='Elastic search endpoint.')
    args = argparser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging ON.")

    quick_umls_service = 'localhost:5000'
    elastic_service = args.elastic_service

    app.run(host='0.0.0.0', port=args.port, use_reloader=True)
