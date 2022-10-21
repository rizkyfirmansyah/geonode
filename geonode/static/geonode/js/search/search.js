'use strict';

(function() {

    var infiniteScrollMsg = `
      <div id="infiniteToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
        <div class="toast-message alert-info align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="toast-header">
            <strong class="mr-auto">End of Content</strong>
            <small class="text-muted"></small>
            <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('infiniteToast').remove()" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="toast-body">
            <span class="font-lg-1">You have reached the end of this content. There's nothing more here.</span>
          </div>
        </div>
      </div>
    `

    var module = angular.module('geonode_main_search', ['ngCookies', 'ngSanitize', 'ui.bootstrap'], function($locationProvider) {
        if (window.navigator.userAgent.indexOf("MSIE") == -1) {
            $locationProvider.html5Mode({
                enabled: true,
                requireBase: false
            });

            // make sure that angular doesn't intercept the page links
            angular.element("a").prop("target", "_self");
        }
    });

    module.config(['$httpProvider', function($httpProvider) {
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    }]);

    // Used to set the class of the filters based on the url parameters
    module.set_initial_filters_from_query = function(data, url_query, filter_param) {
        for (var i = 0; i < data.length; i++) {
            if (url_query == data[i][filter_param] || url_query.indexOf(data[i][filter_param]) != -1) {
                data[i].active = 'active';
            } else {
                data[i].active = '';
            }
        }
        return data;
    }

    // Load categories, keywords, and regions
    module.load_categories = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        $http.get(CATEGORIES_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            var _data = data.data.objects;
            if ($location.search().hasOwnProperty('f4e493d')) {
              _data = module.set_initial_filters_from_query(_data,
                    $location.search()['f4e493d'], 'identifier');
            }
            $rootScope.categories = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            //error code
        };
    }

    // Load group categories
    module.load_group_categories = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        $http.get(GROUP_CATEGORIES_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            $rootScope.groupCategories = data.data.objects;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            //error code
        };
    }

    module.load_keywords = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        $http.get(KEYWORDS_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            var _data = data.data.objects;
            //success code
            $rootScope.keywords = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            //error code
        };
    }

    module.load_t_keywords = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        if (enable_thesauri) {
            $http.get(T_KEYWORDS_ENDPOINT, { params: params }).then(successCallback, errorCallback);
        }

        function successCallback(data) {
            var _data = data.data.objects;
            //success code
            if ($location.search().hasOwnProperty('ebe16ff')) {
                _data = module.set_initial_filters_from_query(_data,
                    $location.search()['ebe16ff'], 'id');
            }
            $rootScope.tkeywords = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            //error code
            console.log(error);
        };
    }

    module.load_regions = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        $http.get(REGIONS_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            var _data = data.data.objects;
            //success code
            $rootScope.regions = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            //error code
        };
    }

    module.load_groups = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        $http.get(GROUPS_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            var _data = data.data.objects;
            $rootScope.groups = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            //error code
        };
    }

    // Load dataset_type
    module.load_dataset_type = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == "undefined" ? {} : { 'type': FILTER_TYPE };
        $http.get(DATASETEXT_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            var _data = data.data.objects;
            $rootScope.dataset_type = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            console.log(error);
        };
    }

    // Load data_type
    module.load_data_type = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == "undefined" ? {} : { 'type': FILTER_TYPE };
        $http.get(DATATYPE_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            var _data = data.data.objects;
            if ($location.search().hasOwnProperty('182243e')) {
              _data = module.set_initial_filters_from_query(_data,
                    $location.search()['182243e'], 'identifier');
            }
            $rootScope.data_type = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            console.log(error);
        };
    }

    // load resource type
    module.load_resource_type = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == "undefined" ? {} : { 'type': FILTER_TYPE };
        $http.get(RESOURCETYPE_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            var _data = data.data.objects;
            $rootScope.resource_types = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        }

        function errorCallback(error) {
            console.log(error);
        }
    }

    module.load_owners = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        $http.get(OWNERS_ENDPOINT, { params: params }).then(successCallback, errorCallback);
        function successCallback(data) {
            var _data = data.data.objects;
            //success code
            $rootScope.owners = _data;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            //error code
        };
    }

    // Update facet counts for categories and keywords
    module.haystack_facets = function($http, $rootScope, $location) {
        var data = $rootScope.query_data;
        if ("categories" in $rootScope) {
            try {
                $rootScope.category_counts = data.meta.facets.category;
                for (var id in $rootScope.categories) {
                    var category = $rootScope.categories[id];
                    if (category.identifier in $rootScope.category_counts) {
                        category.count = $rootScope.category_counts[category.identifier]
                    } else {
                        category.count = 0;
                    }
                }
            } catch (err) {
                // console.log(err);
            }
        }

        if ("data_type" in $rootScope) {
            try {
                $rootScope.data_type_counts = data.meta.facets.data_type;
                for (var id in $rootScope.data_type) {
                    var data_type = $rootScope.data_type[id];
                    if (data_type.identifier in $rootScope.data_type_counts) {
                        data_type.count = $rootScope.data_type_counts[data_type.identifier]
                    } else {
                        data_type.count = 0;
                    }
                }
            } catch (err) {
                // console.log(err);
            }
        }

        if ("dataset_type" in $rootScope) {
            try {
                $rootScope.dataset_type_counts = data.meta.facets.dataset_type;
                for (var id in $rootScope.dataset_type) {
                    var dataset_type = $rootScope.dataset_type[extension];
                    if (dataset_type.extension in $rootScope.data_type_counts) {
                        dataset_type.count = $rootScope.dataset_type_counts[dataset_type.extension]
                    } else {
                        dataset_type.count = 0;
                    }
                }
            } catch (err) {
                // console.log(err);
            }
        }

        if ("keywords" in $rootScope) {
            try {
                $rootScope.keyword_counts = data.meta.facets.keywords;
                for (var id in $rootScope.keywords) {
                    var keyword = $rootScope.keywords[id];
                    if (keyword.slug in $rootScope.keyword_counts) {
                        keyword.count = $rootScope.keyword_counts[keyword.slug]
                    } else {
                        keyword.count = 0;
                    }
                }
            } catch (err) {
                // console.log(err);
            }
        }

        if ("regions" in $rootScope) {
            try {
                $rootScope.regions_counts = data.meta.facets.regions;
                for (var id in $rootScope.regions) {
                    var region = $rootScope.regions[id];
                    if (region.name in $rootScope.region_counts) {
                        region.count = $rootScope.region_counts[region.name]
                    } else {
                        region.count = 0;
                    }
                }
            } catch (err) {
                // console.log(err);
            }
        }

        if ("owners" in $rootScope) {
            try {
                $rootScope.owner_counts = data.meta.facets.owners;
                for (var id in $rootScope.owners) {
                    var owner = $rootScope.owners[id];
                    if (owner.name in $rootScope.owner_counts) {
                        owner.count = $rootScope.owner_counts[owner.name]
                    } else {
                        owner.count = 0;
                    }
                }
            } catch (err) {
                // console.log(err);
            }
        }
    }

    /*
     * Bind an event to load infinite to display catalogue
     */
    module.directive("infiniteScrollDirective", function() {
        return function(scope, elm, attr) {
          if (scope.infiniteScrollLoaded)
              $(window).on('scroll', function() {
                  if ($(window).scrollTop() + $(window).height() == $(document).height()) {
                      setTimeout(function() {
                          scope.$apply(attr.infiniteScrollDirective);
                          scope.infiniteScroll++;
                      }, 500);
                  }
              })
        }
    })

    /*
     * Load categories and keywords
     */
    module.run(function($http, $rootScope, $location) {
        /*
         * Load categories and keywords if the filter is available in the page
         * and set active class if needed
         */
        // search.init();
        if ($('#categories').length > 0) {
            module.load_categories($http, $rootScope, $location);
        }

        if ($('#group-categories').length > 0) {
            module.load_group_categories($http, $rootScope, $location);
        }

        if ($('#keywords').length > 0) {
            module.load_keywords($http, $rootScope, $location);
        }

        // module.load_h_keywords($http, $rootScope, $location);

        if ($('#regions').length > 0) {
            module.load_regions($http, $rootScope, $location);
        }
        if ($('#owners').length > 0) {
            module.load_owners($http, $rootScope, $location);
        }
        if ($('#groups').length > 0) {
            module.load_groups($http, $rootScope, $location);
        }
        if ($('#tkeywords').length > 0) {
            module.load_t_keywords($http, $rootScope, $location);
        }
        if ($('#data_type').length > 0) {
            module.load_data_type($http, $rootScope, $location);
        }
        if ($('#resource_type').length > 0) {
            module.load_resource_type($http, $rootScope, $location);
        }
        if ($('#dataset_type').length > 0) {
            module.load_dataset_type($http, $rootScope, $location);
        }

        // Activate the type filters if in the url
        if ($location.search().hasOwnProperty('type__in')) {
            var types = $location.search()['type__in'];
            if (types instanceof Array) {
                for (var i = 0; i < types.length; i++) {
                    $('body').find("[data-filter='type__in'][data-value=" + types[i] + "]").addClass('active');
                }
            } else {
                $('body').find("[data-filter='type__in'][data-value=" + types + "]").addClass('active');
            }
        }

        // Activate the sort filter if in the url
        if ($location.search().hasOwnProperty('order_by')) {
            var sort = $location.search()['order_by'];
            $('body').find("[data-filter='order_by']").removeClass('selected');
            $('body').find("[data-filter='order_by'][data-value=" + sort + "]").addClass('selected');
        }

    });

    /*
     * Main search controller
     * Load data from api and defines the multiple and single choice handlers
     * Syncs the browser url with the selections
     */
    module.controller('geonode_search_controller', function($injector, $scope, $rootScope, $location, $http, Configs) {
        $scope.query = $location.search();
        $scope.infiniteScroll = 0;
        $scope.infiniteScrollLoaded = true;
        $scope.filter = false;
        $scope.reset = false;
        $scope.init = true;
        $scope.page = 0;
        $scope.is_next = true;
        $scope.loadMoreResource = function() {
            const _infinite = new Promise(function(resolve, reject) {
                if ($scope.infiniteScrollLoaded) {
                    query_api($scope.query);
                }
                resolve(true);
            });
        };

        //Get data from apis and make them available to the page
        function query_api(data) {
            // handling for infinite scroll at the catalogue browse without filtered is true
            if (jQuery.isEmptyObject(data)) {
              if (!$scope.results && $scope.init) {
                  $scope.page = 1;
              }
              data = { page: $scope.page }
            } else {
                // handling for filter is true
                if ($scope.init) {
                    $scope.page = 1;
                }
                data.page = $scope.page;
            }

            $http.get(Configs.url, { params: data || {} }).then(successCallback, errorCallback)

            function successCallback(data) {
                //success code
                setTimeout(function() {
                    $('[ng-controller="CartList"] [data-toggle="tooltip"]').tooltip();
                }, 0);
                var result = data.data.total;

                if (result === 0) {
                    $scope.infiniteScrollLoaded = false;
                }

                if (!$scope.filter) {
                    if (!$scope.results && $scope.init) {
                        // Initialize the data
                        $scope.results = data.data.objects;
                        $scope.init = false;
                    } else if ($scope.init) {
                        $scope.results = data.data.objects;
                        $scope.init = false;
                    } else if ($scope.is_next) {
                        $scope.results.push(...data.data.objects);
                    }
                } else {
                    if ($scope.init) {
                        $scope.init = false;
                        $scope.results = data.data.objects;
                    }
                     else if ($scope.is_next) {
                        $scope.results.push(...data.data.objects);
                    }
                }

                $scope.total_counts = data.data.total;
                $scope.$root.query_data = data.data;
                if (HAYSTACK_SEARCH) {
                    if ($location.search().hasOwnProperty('q')) {
                        $scope.text_query = $location.search()['q'].replace(/\+/g, " ");
                    }
                }

                //Update facet/keyword/category counts from search results
                if (HAYSTACK_FACET_COUNTS) {
                    try {
                        module.haystack_facets($http, $scope.$root, $location);
                        $("#types").find("a").each(function() {
                            if ($(this)[0].id in data.data.meta.facets.subtype) {
                                $(this).find("span").text(data.data.meta.facets.subtype[$(this)[0].id]);
                            } else if ($(this)[0].id in data.data.meta.facets.type) {
                                $(this).find("span").text(data.data.meta.facets.type[$(this)[0].id]);
                            } else {
                                $(this).find("span").text("0");
                            }
                        });
                    } catch (err) {
                        // console.log(err);
                    }
                }

                $scope.is_next = data.data.links.next;
                if (!$scope.is_next) {
                    $scope.infiniteScrollLoaded = false;
                    if ($scope.page > 1) {
                      setTimeout(function() {
                        $(document.body).append(infiniteScrollMsg);
                        setTimeout(function() {
                          $('#infiniteToast').remove();
                        }, 4000);
                      }, 3000);
                    }
                } else if ($scope.is_next) {
                    $scope.page += 1;
                } 
            };

            function errorCallback(error) {
                //error code
            };
        };

        query_api($scope.query);

        if (!Configs.hasOwnProperty("disableQuerySync")) {
            // Keep in sync the page location with the query object
            $scope.$watch('query', function() {
                $location.search($scope.query);
            }, true);
        }

        /*
         * Add the selection behavior to the element, it adds/removes the 'active' class
         * and pushes/removes the value of the element from the query object
         */
        $scope.multiple_choice_listener = function($event, selected) {
            $scope.infiniteScrollLoaded = true;
            $scope.filter = true;
            $scope.page = 1;
            $scope.init = true;
            $scope.infiniteScroll = 0;
            
            var element = $($event.currentTarget);
            var type = $event.currentTarget.type;
            var type_id = $event.currentTarget.id;
            var query_entry = [];
            var data_filter = element.attr('data-filter');
            var value = element.attr('data-value');

            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter) && type != 'select-multiple') {
                // When in the location are passed two filters of the same
                // type then they are put in an array otherwise is a single string
                if ($scope.query[data_filter] instanceof Array) {
                    query_entry = $scope.query[data_filter];
                } else {
                    query_entry.push($scope.query[data_filter]);
                }
            }

            // If the element is active then deactivate it
            if (element.hasClass('active') && type != 'select-multiple') {
                // clear the active class from it
                element.removeClass('active');
                $scope.page = 1;
                // Remove the entry from the correct query in scope
                query_entry.splice(query_entry.indexOf(value), 1);
            }
            // if is not active then activate it
            else if (!element.hasClass('active') && type != 'select-multiple') {
                // Add the entry in the correct query
                if (query_entry.indexOf(value) == -1) {
                    query_entry.push(value);
                }
                element.addClass('active');
            }
            if (type === 'select-multiple') {
                if (type_id === 'keywords') {
                    data_filter = '7e31fcb';
                } else if (type_id === 'owners') {
                    data_filter = '225d70a'
                }  else if (type_id === 'groups') {
                    data_filter = '5af2a45'
                }
                if (selected.length != 0) {
                    query_entry = selected;
                }
                $scope.query[data_filter] = query_entry;
                if (query_entry.length == 0) {
                    delete $scope.query['7e31fcb']
                    delete $scope.query['225d70a']
                    delete $scope.query['5af2a45']
                }
            } else {
                //save back the new query entry to the scope query
                $scope.query[data_filter] = query_entry;
            }

            if (!$scope.reset) {
                query_api($scope.query);
            }
        }

        $scope.single_choice_listener = function($event, selected) {
            var element = $($event.currentTarget);
            var query_entry = [];
            var data_filter = element.attr('data-filter');
            var value = element.attr('data-value');
            var type = $event.currentTarget.type;
            var type_id = $event.currentTarget.id;

            $scope.filter = true;
            $scope.init = true;
            // Type of data being displayed, use 'content' instead of 'all'
            $scope.dataValue = (value == 'all') ? 'content' : value;
            $scope.page = 1;
            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter)) {
                query_entry = $scope.query[data_filter];
            }

            if (type === 'select-one') {
                if (type_id === 'regions') {
                    data_filter = '90ca628';
                    if (selected) {
                        value = selected;
                        $scope.query[data_filter] = selected;
                        query_api($scope.query);
                    }
                }
            }

            if (!element.hasClass('selected')) {
                // Add the entry in the correct query
                query_entry = value;

                // clear the active class from it
                element.parents('ul').find('a').removeClass('selected');

                element.addClass('selected');

                //save back the new query entry to the scope query
                $scope.query[data_filter] = query_entry;

                if (!$scope.reset) {
                  query_api($scope.query);
                }
            }
        }

        $('#text_search_btn').on('click', function(e) {
            if (HAYSTACK_SEARCH) {
                $scope.query['q'] = $('#text_search_input').val();
            }
            fetch_results();
        });

        $('#text_search_input').on('keypress', function(e) {
            if (e.which == 13) {
                fetch_results();
                var text_search = $("#text_search_input").val();
                setTimeout(function() {
                  if (text_search) {
                      var found = $scope.total_counts + " datasets found for \"" + text_search +'"';
                      $("#dataset-found").text(found);
                  };
                  $(".ac-results").addClass("d-none");
                }, 500);
            }
        })

        function fetch_results() {
            if (HAYSTACK_SEARCH) {
              $scope.query['q'] = $('#text_search_input').val();
            }
            if ($('#text_search_input').val()) {
              $scope.infiniteScrollLoaded = true;
              $scope.init = true;
              $scope.query['dbbc87e'] = $('#text_search_input').val();
              query_api($scope.query);
              
            } else {
                reset_query();
            }
        }

        function reset_query() {
            if (HAYSTACK_SEARCH) {
                $scope.query['q'] = $('#text_search_input').val('');
            }
            $scope.query = {};
            $scope.infiniteScroll = 0;
            $scope.infiniteScrollLoaded = false;
            $scope.filter = false;
            $scope.init = true;
            $scope.reset = true;
            // remove active class elements from sidebar
            $('.selectpicker').selectpicker('val', '');
            $('.selectpicker').selectpicker('refresh');
            $('.span_count').parent().addClass('w-100 m-0 d-inline-block');
            $('#filter-sidebar-content .btn_wrapper').removeClass('active');
            $('#filter-sidebar-content .btn_wrapper').find('input[type=checkbox]:checked').prop("checked", false);
            $(".scrollbar-sidebar a").removeClass("active");
            $(".filter a").removeClass("active");
            $("#text_search_input").val('');
            delete $scope.query['7e31fcb'];
            delete $scope.query['225d70a'];
            delete $scope.query['5af2a45'];
            delete $scope.query['90ca628'];
            delete $scope.query['page'];
            delete $scope.query['c'];
            $location.search($scope.query);
            if ($location.path().includes("group")) {
                return query_api($scope.query);
            }
        }

        $('.clear_filter').on('click', function(e) {
            e.preventDefault();
            reset_query();
            $scope.reset = false;
            $scope.infiniteScrollLoaded = true;
        });

        $("#dltDate1").on('click', function (e) {
            $scope.date_query = {
                'date__gte': '',
                'date__lte': '',
                'date__range': ''
            };
            reset_query();
            $("#inpDate1").val('');
        });

        $("#dltDate2").on('click', function (e) {
            $scope.date_query = {
                'date__gte': '',
                'date__lte': '',
                'date__range': ''
            };
            reset_query();
            $("#inpDate2").val('');
        });

        $scope.feature_select = function($event) {
            var element = $(event.currentTarget);
            var article = $(element.parents('article')[0]);
            if (article.hasClass('resource_selected')) {
                element.html('Select');
                article.removeClass('resource_selected');
            } else {
                element.html('Deselect');
                article.addClass('resource_selected');
            }
        };

        /*
         * Date management
         */

        $scope.date_query = {
            'date__gte': '',
            'date__lte': ''
        };
        var init_date = true;
        $scope.$watch('date_query', function() {
            if ($scope.date_query.date__gte != '' && $scope.date_query.date__lte != '') {
                var dateGte = $scope.date_query.date__gte;
                var dateLte = $scope.date_query.date__lte;
                $scope.query['date__range'] = dateGte + ',' + dateLte;
                delete $scope.query['date__gte'];
                delete $scope.query['date__lte'];
            } else if ($scope.date_query.date__gte != '') {
                var dateGte = $scope.date_query.date__gte;
                $scope.query['date__gte'] = dateGte;
                delete $scope.query['date__range'];
                delete $scope.query['date__lte'];
            } else if ($scope.date_query.date__lte != '') {
                var dateLte = $scope.date_query.date__lte;
                $scope.query['date__lte'] = dateLte;
                delete $scope.query['date__range'];
                delete $scope.query['date__gte'];
            } else {
                delete $scope.query['date__range'];
                delete $scope.query['date__gte'];
                delete $scope.query['date__lte'];
            }
            if (!init_date) {
                $scope.infiniteScrollLoaded = true;
                $scope.init = true;
                query_api($scope.query);
            } else {
                init_date = false;
            }

        }, true);

        /*
         * Spatial search
         */
        if ($('.leaflet_map').length > 0) {
            angular.extend($scope, {
                layers: [{
                    name: 'OpenStreetMap',
                    active: true,
                    source: {
                        type: 'OSM'
                    }
                }],
                center: {
                    lat: 0.0,
                    lon: 0.0,
                    zoom: 1
                },
                defaults: {
                    interactions: {
                        mouseWheelZoom: true
                    },
                    controls: {
                        zoom: {
                            position: 'topleft'
                        }
                    }
                }
            });

            var olData = $injector.get('olData'),
                map = olData.getMap('filter-map');

            map.then(function(map) {
                map.on('moveend', function() {
                    var glbox = map.getView().calculateExtent(map.getSize()); // doesn't look as expected.
                    var box = ol.proj.transformExtent(glbox, 'EPSG:3857', 'EPSG:4326');
                    $scope.query['extent'] = box.toString();
                    query_api($scope.query);
                });
            });

            var showMap = false;
            $('#_extent_filter').click(function(evt) {
                showMap = !showMap
                if (showMap) {
                    olData.getMap().then(function(map) {
                        map.updateSize();
                    });
                }
            });
        }
    });

    module.config(['$httpProvider', function($httpProvider) {
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    }]);

    module.filter('humanFileSize', function() {
        'use strict';

        return function(bytes, si=false, dp=1) {
            const thresh = si ? 1000 : 1024;
          
            if (Math.abs(bytes) < thresh) {
              return bytes + ' B';
            }
          
            const units = si 
              ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'] 
              : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
            let u = -1;
            const r = 10**dp;
          
            do {
              bytes /= thresh;
              ++u;
            } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);
          
          
            return bytes.toFixed(dp) + ' ' + units[u];
        }
    });

    module.filter("titleCase", function () {
      return function (input) {
        input = input || '';
        return input.replace(/_/g, " ").replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
      }
    });

})();