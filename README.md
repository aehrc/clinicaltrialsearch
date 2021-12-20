# Clinical Trials Search


## About the project

A search engine for retrieving clinical trials.



## Setup


### Deployment Model

The backend search engine is Elasticsearch.

There are two different deployment options:

1. **Docker** - A complete docker based solution as define in `docker-compose.yml` that starts up all the different components; or
2. **Standalone** - Individual components can be started separately.




### Elastic Setup (Standalone only)

Using docker:

```
$ docker run --name es-clinicaltrials-5-2020 -p 9200:9200 \
	-e "http.host=0.0.0.0" -e "xpack.security.enabled=false" -e "transport.host=127.0.0.1" \
	-v plexa-elastic-index:/usr/share/elasticsearch/data \
	docker.elastic.co/elasticsearch/elasticsearch:5.0.2
```

### Indexing (Both)

This is done regardless of the deployment model.

##### Running the trials indexer

Clinical trial documents are distributed in a specific [XML format](https://clinicaltrials.gov/ct2/resources/download). Getting these document indexed by Elastic is done via the `indexer` Java module. Indexer will do the following:

1. Convert the XML into JSON format. Batches of 1,000 clinicial trials will be written to the `json_out` directory.
2. Submit the JSON batches to Elastic at the following endpoint: [http://localhost:9200/clinicaltrials/](http://localhost:9200/clinicaltrials/)


To run the indexer:

```
$ ./indexer/bin/indexer.sh <corpus-dir>
```

where `corpus-dir` is the path where all the clinical trial XML documents are found.

##### Clearing an existing index

The `indexer` assumes that no index exists and will attempt to create a `clinicaltrials` index. To delete the entire index call:

```
$ curl -XDELETE http://localhost:9200/clinicaltrials
```

### Searching using the Matcher (Standalone only)


#### Standalone option

For search on the command line:

```
$ python matcher/matcher.py -h
```

The search service requires the use of QuickUMLS REST. The easiest way to get this is via the docker hub: [https://cloud.docker.com/u/aehrc/repository/docker/aehrc/quickumls-rest](https://cloud.docker.com/u/aehrc/repository/docker/aehrc/quickumls-rest). The command to start is:

```
$ docker run -d --name quickumls-rest -p 5000:5000 aehrc/quickumls-rest:1.2.3-2018AA
```

For the REST service:

```
$ python matcher/matcher-rest_service.py --port 8888 
```
This will start the REST service on [http://localhost:8888](http://localhost:8888) (change port accordingly). You can `HTTP POST` to this but also visit the address to get a handy web site for testing.

### Searching using the Matcher (Docker only)

The docker compose will start 1) Elasticsearch 2) QuickUMLS 3) Matcher; all in one. This is the easiest way to deploy. The `docker-compuse.yml` contains the definitions for these. The command to start all this is:

```
$ docker-compose up
```

After this:

* Elastic will be running on [http://localhost:9200](http://localhost:9200)
* QuickUMLS will be running on [http://localhost:5000](http://localhost:5000)
* The Matcher service will be running on [http://localhost:8888](http://localhost:8888)

### Webapp (Experimental)

The webapp is a AngularJS application found in the `webapp` directory in Git.

Set the endpoint of elastic search in `config.js`:

```
var elasticsearchEndpoint = 'localhost:9200/clinicaltrials';
var enableLogging = true;
```

The webapp need to run within a webserver.

## Development Environment

The project uses Python Anaconda environment management. The environment is defined in `environment.yml`. To setup a new environment run:

```
$ conda env create -f environment.yml
```

This will create a new environment called `clinicaltrials-env` and install all the required python dependencies. Activate the new enviroment via:

```
$ conda activate clinicaltrials-env
```
## Compiling (docker)

The `matcher` is a standalone component that can be dockerised by running the following in the `matcher` dir:

```{bash}
$ docker build -t docker-registry.it.csiro.au/health-text-analytics/clinicaltrials-matcher:0.0.2 .
```
Replace `0.0.2` with correct version number.

## API Documentation

The REST API is accessed by submitting an HTTP POST to

```json
http://host:port/
with JSON:
{
  "query" :  "you text here",
  "num_results": 10,
  "recruiting_only": false,
  "country": "your country here - blank for all",
  <any_field>: <value>
}
```
					
Optional arguments include:
- `num_results`: number of results to return (default: 10).
- `recruiting_only`: return only trials with status as recruiting (default: false).
- `country`: return only trials with in the specified country (default: show all countries).

In addition, you can filter by any field and value but specifying it as a param in the request. Ensure that the field matches extactly as that shown in the response; e.g., `"responsible_party.organization": "responsible_party"` where the `organization` field is nested within the `responsible_party` field.
Some sample patient records are also provided by HTTP GET to `/patient` or `/patient/<patient_id>`.