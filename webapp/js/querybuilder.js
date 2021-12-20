

(function() {

	var app = angular.module('querybuilder', []);



	this.buildQuery = function(queryTerms, filter, begin) {


		queryTerms = queryTerms.replace(/\+/i, "AND");
		queryTerms = queryTerms.replace(/\-/i, "NOT ");
		queryTerms = queryTerms.replace(/and/i, "AND");
		queryTerms = queryTerms.replace(/or/i, "OR");
		
		var query =  {
			"from" : begin, "size" : 100,
			"query": {
				"query_string" : {
					"query": queryTerms
				}
			},
			"highlight" : {
				"pre_tags" : ["<span class='snippet'>"],
				"post_tags" : ["</span>"],
				"fields" : {
					"*" : {}
				},
				"require_field_match" : false
			},
			"aggs": {
				"modality_count" : { "terms" : { "field" : "MODALITY" } }, 
				"author_count" : { "terms" : { "field" : "AUTHOR" } }, 
				"age_count" : { "histogram" : { "field" : "AGE", "interval": "10" } }, 
				"gender_count" : { "terms" : { "field" : "PATIENT_SEX" } } 
			}
		};

		return query;
	};

	
})();
