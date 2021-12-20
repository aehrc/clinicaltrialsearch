

(function() {

	var app = angular.module('logger', []);

	//app.controller('SearchController', ['$scope', '$http', '$log', 'searchResultsService', function($scope, $http, $log, searchResultsService){

	this.logger = function(task, queryTerms, value) {
		if(enableLogging) {
			var currentdate = new Date(); 
			var datetime = currentdate.getDate() + "/" + (currentdate.getMonth()+1)  + "/"  + currentdate.getFullYear() + " @ "  
				+ currentdate.getHours() + ":" + currentdate.getMinutes() + ":" + currentdate.getSeconds();
			$.post( "http://"+elasticsearchEndpoint+"/radiology/logs", '{ task: "'+task+'", query: "'+queryTerms+'", timestamp: "'+datetime+'", value: "'+value+'" }', function() {
				})
				.fail(function(err) {
					console.log( "Unable to log the query: "+err.responseText);
				});
		}
	};

	
})();
