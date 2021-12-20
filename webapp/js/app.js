

(function() {

	var app = angular.module('searchApp', ['ui.bootstrap', 'chart.js', 'infinite-scroll', 'querybuilder', 'logger']);

	app.factory('searchResultsService', function(){
		var searchResults = {};

		searchResults.results = {};

		searchResults.setResults = function(res){
			results = res;
		};

		return searchResults;
	});




	// simple controller to get the collections size and pass through to view
	app.controller('MetadataController', ['$http', function($http){
		this.collectionSize = 0;

		var metadataCtrl = this;
		$http.get('http://'+elasticsearchEndpoint+'/_count').success(function(data) {
			metadataCtrl.collectionSize = data.count;
		});

	}]);


	// main controller used to hit the elasticsearch backend and pass through results to view
	app.controller('SearchController', ['$scope', '$http', '$log', 'searchResultsService', function($scope, $http, $log, searchResultsService){
		searchCtrl = this;

		this.queryTerms = "";
		this.results = {};
		this.errors = "";
		searchCtrl.charts = false;

		this.random = parseInt(Math.random()*100000000,10);

		// hit the elastic search backend via HTTP
		this.doSearch = function(queryTerms, filter, begin) {
			var query = buildQuery(queryTerms, filter);
			logger("search", queryTerms, queryTerms);





			$http.post('http://'+elasticsearchEndpoint+'/_search', query, { headers : {'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8'} } ).
				success(function(data, status, headers, config) {
					searchCtrl.errors = "";
					searchCtrl.results = data;		
					searchCtrl.fillCharts(data.aggregations);
					searchCtrl.charts = true;


				}).
				error(function(data, status, headers, config, statusText) {
					$log.info(data);
					searchCtrl.errors = headers;
				});
		};


		$scope.paginateResults = function() {
	    $log.info("more results");
	    searchCtrl.doSearch(searchCtrl.queryTerms, "", 100);
	  };

		$scope.modalityFilter = function(points, evt) {
      var modality = points[0].label.toLowerCase();
      searchCtrl.queryTerms = searchCtrl.queryTerms + " AND MODALITY:"+modality;
      modalityFilter = {"term": {"MODALITY": modality}};
      searchCtrl.doSearch(searchCtrl.queryTerms, modalityFilter, 0);
    };

    $scope.ageFilter = function(points, evt) { //AGE:(>=90 AND <120)
      var age = parseInt(points[0].label);
      searchCtrl.queryTerms = searchCtrl.queryTerms + " AND AGE:(>="+age+" AND <"+(age+10)+")";
      searchCtrl.doSearch(searchCtrl.queryTerms, 0);
    };

    $scope.sexFilter = function(points, evt) {
      var sex = points[0].label.substr(0,1);
      searchCtrl.queryTerms = searchCtrl.queryTerms + " AND PATIENT_SEX:"+sex;
      searchCtrl.doSearch(searchCtrl.queryTerms, 0);
    };

    $scope.authorFilter = function(points, evt) {
      var author = points[0].label.toLowerCase();
      searchCtrl.queryTerms = searchCtrl.queryTerms + " AND AUTHOR:"+author;
      authorFilter = {"term": {"AUTHOR": author}};
      searchCtrl.doSearch(searchCtrl.queryTerms, authorFilter, 0);
    };


		// populate all the facet charts
		this.fillCharts = function(aggs) {
			$scope.modalitychart = searchCtrl.prepareChartData(aggs.modality_count['buckets'], "rgba(224, 108, 112, 1)", "rgba(207,100,103,1)"); // 15, 8, 9, 0
			$scope.agechart = searchCtrl.prepareChartData(aggs.age_count['buckets'], 'rgba(253,180,92,1)', 'rgba(233,175,80,1)');
			$scope.genderchart = searchCtrl.prepareChartData(aggs.gender_count['buckets'], "rgba(224, 108, 112, 1)", "rgba(207,100,103,1)");
			$scope.authorchart = searchCtrl.prepareChartData(aggs.author_count['buckets'], "rgba(77,83,96,1)", "rgba(62,75,87,1)");
		};

		this.prepareChartData = function(buckets, fillColor, strokeColor) {
			var keys = [];
			var values = [];
			for(i=0; i<buckets.length; i++) {
				keys.push(buckets[i]['key'].toString().toUpperCase() );
				values.push(buckets[i]['doc_count']);
			}

			var chart_data = {
        "data": [values],
        "labels": keys,
        "colours": [{
          "fillColor": fillColor,
          "strokeColor": strokeColor
        }]
      };

      return chart_data;
		};

	}]);

	// controller for a single patient, displayed via modal box
	app.controller('PatientDetailsCtrl', function ($scope, $modal, $log) {

		$scope.patient = '';

		$scope.open = function (patient, queryTerms) {

			$scope.patient = patient;

			logger("patient", queryTerms, patient._source.ACCESSION_NUMBER);

			var modalInstance = $modal.open({
				templateUrl: 'myModalContent.html',
				controller: 'PatientDetailsInstanceCtrl',
				size: 'lg',
				resolve: {
					patient: function () {
						return $scope.patient;
					}
				}
			});

			modalInstance.result.then(function (selectedItem) {
				
			}, function () {
				//$log.info('Modal dismissed at: ' + new Date());
			});
		};
	
	});

	// the modal box of a single patient, referenced by PatientDetailsCtrl
	app.controller('PatientDetailsInstanceCtrl', function ($scope, $modalInstance, patient) {
		$scope.patient = patient;
		$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
		};
	});


	// Custom HTML element directives below

	app.directive('searchForm', function() {
		return {
			restrict: 'E',
			templateUrl: 'search_form.html'
		};
	});
	app.directive('searchResults', function() {
		return {
			restrict: 'E',
			templateUrl: 'search_results.html'
		};
	});
	app.directive('patientDetails', function() {
		return {
			restrict: 'E',
			templateUrl: 'patient_details.html'
		};
	});
	app.directive('help', function() {
		return {
			restrict: 'E',
			templateUrl: 'help.html'
		};
	});

	// set the initial keyboard focus to a specific HTML element
	// set via "focus" attribute, e.g., <input focus="true">
	app.directive('focus', function($timeout) {
		return {
			scope : {
				trigger : '@focus'
			},
			link : function(scope, element) {
				scope.$watch('trigger', function(value) {
					if (value === "true") {
						$timeout(function() {
							element[0].focus();
						});
					}
				});
			}
		};
	}); 
	
 

	// expression filter to allow HTML content through to the view
	app.filter("sanitize", ['$sce', function($sce) {
		return function(htmlCode){
			return $sce.trustAsHtml(htmlCode);
		}
	}]);

	
})();
