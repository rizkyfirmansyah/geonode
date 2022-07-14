'use strict';

(function() {


    // hide the autocomplete div results whenever the users click on container
    $('.container').on('click', function(){
        $('.ac-results').addClass("d-none");
    });

    var module = angular.module('geonode_main_search', ['ngCookies', 'ngSanitize'], function($locationProvider) {
        if (window.navigator.userAgent.indexOf("MSIE") == -1) {
            $locationProvider.html5Mode({
                enabled: true,
                requireBase: false
            });

            // make sure that angular doesn't intercept the page links
            angular.element("a").prop("target", "_self");
        }
    });

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
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        params['limit'] = 0;
        $http.get(CATEGORIES_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('category__identifier__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['category__identifier__in'], 'identifier');
            }
            $rootScope.categories = data.data.objects;
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
        params['limit'] = 0;
        $http.get(KEYWORDS_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            $rootScope.keywords = data.data.objects;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            //error code
        };
    }


    module.load_h_keywords = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        $http.get(H_KEYWORDS_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            $('#treeview').treeview({
                data: data.data,
                multiSelect: true,
                showIcon: true,
                showCheckbox: false,
                collapseIcon: false,
                expandIcon: false,
                showTags: true,
                tagsClass: 'badge',
                onNodeSelected: function($event, node) {
                    $rootScope.$broadcast('select_h_keyword', node);
                    if (node.nodes) {
                        for (var i = 0; i < node.nodes.length; i++) {
                            $('#treeview').treeview('selectNode', node.nodes[i]);
                        }
                    }
                },
                onNodeUnselected: function($event, node) {
                    $rootScope.$broadcast('unselect_h_keyword', node);
                    if (node.nodes) {
                        for (var i = 0; i < node.nodes.length; i++) {
                            $('#treeview').treeview('unselectNode', node.nodes[i]);
                            $('#treeview').trigger('nodeUnselected', $.extend(true, {}, node.nodes[i]));
                        }
                    }
                }
            });
        };

        function errorCallback(error) {
            //error code
            console.log(error);
        };
    };

    module.load_t_keywords = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        if (enable_thesauri) {
            $http.get(T_KEYWORDS_ENDPOINT, { params: params }).then(successCallback, errorCallback);
        }

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('tkeywords__id__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['tkeywords__id__in'], 'id');
            }
            $rootScope.tkeywords = data.data.objects;
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
        params['limit'] = 0;
        $http.get(REGIONS_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('regions__name__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['regions__name__in'], 'name');
            }
            $rootScope.regions = data.data.objects;
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
        params['limit'] = 0;
        $http.get(GROUPS_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            $rootScope.groups = data.data.objects;
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
            if ($location.search().hasOwnProperty('link__extension__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['link__extension__in'], 'extension');
            }
            $rootScope.dataset_type = data.data.objects;
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
            if ($location.search().hasOwnProperty('data_type__identifier__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['data_type__identifier__in'], 'identifier');
            }
            $rootScope.data_type = data.data.objects;
            if (HAYSTACK_FACET_COUNTS && $rootScope.query_data) {
                module.haystack_facets($http, $rootScope, $location);
            }
        };

        function errorCallback(error) {
            console.log(error);
        };
    }

    module.load_owners = function($http, $rootScope, $location) {
        var params = typeof FILTER_TYPE == 'undefined' ? {} : { 'type': FILTER_TYPE };
        if ($location.search().hasOwnProperty('title__icontains')) {
            params['title__icontains'] = $location.search()['title__icontains'];
        }
        params['limit'] = 0;
        $http.get(OWNERS_ENDPOINT, { params: params }).then(successCallback, errorCallback);

        function successCallback(data) {
            //success code
            if ($location.search().hasOwnProperty('owner__username__in')) {
                data.data.objects = module.set_initial_filters_from_query(data.data.objects,
                    $location.search()['owner__username__in'], 'identifier');
            }
            $rootScope.owners = data.data.objects;
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

        module.load_h_keywords($http, $rootScope, $location);

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
    module.controller('geonode_search_controller', function($injector, $scope, $location, $http, Configs) {
        $scope.query = $location.search();
        $scope.infiniteScroll = 0;
        $scope.infiniteScrollLoaded = true;
        $scope.filter = false;
        $scope.init = true;
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
                  $scope.offset = 0;
              } else {
                  if (!$scope.init) {
                      $scope.offset += API_LIMIT_PER_PAGE;
                  }
              }
              data = { offset: $scope.offset}
            } else {
                // handling for filter is true
                if (!$scope.init) {
                    $scope.offset += API_LIMIT_PER_PAGE;
                } else {
                    $scope.offset = 0;
                }

                for (var key in data) {
                  if (!$scope.filter) {
                      // handling for filter is not available
                      if (key.includes("_in") && !$scope.offset) {
                        $scope.offset = 0;
                        $scope.filter = true;
                    }
                  }
                }
                data.offset = $scope.offset;
            }

            $http.get(Configs.url, { params: data || {} }).then(successCallback, errorCallback)

            function successCallback(data) {
                //success code
                setTimeout(function() {
                    $('[ng-controller="CartList"] [data-toggle="tooltip"]').tooltip();
                }, 0);
                var result = data.data.objects.length;

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
                    } else {
                        $scope.results.push(...data.data.objects);
                    }
                } else {
                    if ($scope.init) {
                        $scope.init = false;
                        $scope.results = data.data.objects;
                    } else {
                        $scope.results.push(...data.data.objects);
                    }
                }

                $scope.total_counts = data.data.meta.total_count;
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

                var meta = data.data.meta;
                if (meta.limit >= meta.total_count) {
                  $scope.infiniteScrollLoaded = false;
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

        // Hierarchical keyword listeners
        $scope.$on('select_h_keyword', function($event, element) {
            var data_filter = 'keywords__slug__in';
            var query_entry = [];
            var value = (element.href ? element.href : element.text);
            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter)) {

                // When in the location are passed two filters of the same
                // type then they are put in an array otherwise is a single string
                if ($scope.query[data_filter] instanceof Array) {
                    query_entry = $scope.query[data_filter];
                } else {
                    query_entry.push($scope.query[data_filter]);
                }
            }

            // Add the entry in the correct query
            if (query_entry.indexOf(value) == -1) {
                query_entry.push(value);
            }

            //save back the new query entry to the scope query
            $scope.query[data_filter] = query_entry;

            query_api($scope.query);
        });

        $scope.$on('unselect_h_keyword', function($event, element) {
            var data_filter = 'keywords__slug__in';
            var query_entry = [];
            var value = (element.href ? element.href : element.text);
            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter)) {

                // When in the location are passed two filters of the same
                // type then they are put in an array otherwise is a single string
                if ($scope.query[data_filter] instanceof Array) {
                    query_entry = $scope.query[data_filter];
                } else {
                    query_entry.push($scope.query[data_filter]);
                }
            }

            query_entry.splice(query_entry.indexOf(value), 1);

            //save back the new query entry to the scope query
            $scope.query[data_filter] = query_entry;

            //if the entry is empty then delete the property from the query
            if (query_entry.length == 0) {
                delete($scope.query[data_filter]);
            }
            query_api($scope.query);
        });

        /*
         * Add the selection behavior to the element, it adds/removes the 'active' class
         * and pushes/removes the value of the element from the query object
         */
        $scope.multiple_choice_listener = function($event, selected) {
            $scope.infiniteScrollLoaded = true;
            $scope.filter = true;
            $scope.offset = 0;
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
                $scope.offset = 0;
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
                    data_filter = 'keywords__slug__in'
                } else if (type_id === 'owners') {
                    data_filter = 'owner__username__in'
                }
                if (selected.length != 0) {
                    value = selected;
                    query_entry = selected;
                }
                $scope.query[data_filter] = query_entry;
                if (selected.length == 0)
                    delete $scope.query['keywords__slug__in']
            } else {
                //save back the new query entry to the scope query
                $scope.query[data_filter] = query_entry;
            }
            
            query_api($scope.query);
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
            $scope.offset = 0;
            // If the query object has the record then grab it
            if ($scope.query.hasOwnProperty(data_filter)) {
                query_entry = $scope.query[data_filter];
            }

            if (type === 'select-one') {
                if (type_id === 'regions') {
                    data_filter = 'regions__name__in';
                }
                if (selected) {
                    value = selected;
                }
                $scope.query[data_filter] = selected;

                query_api($scope.query);
            }

            if (!element.hasClass('selected')) {
                // Add the entry in the correct query
                query_entry = value;

                // clear the active class from it
                element.parents('ul').find('a').removeClass('selected');

                element.addClass('selected');

                //save back the new query entry to the scope query
                $scope.query[data_filter] = query_entry;

                query_api($scope.query);
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
            }
        })

        $('#region_search_btn').on('click', function(e) {
            if ($('#region_search_input').val()) {
                $scope.query['regions__name__in'] = $('#region_search_input').val();
            } else {
                delete $scope.query['regions__name__in']
            }
            $scope.infiniteScrollLoaded = true;
            $scope.init = true;
            query_api($scope.query);
        });

        function fetch_results() {
            if (HAYSTACK_SEARCH) {
              $scope.query['q'] = $('#text_search_input').val();
            }
            if ($('#text_search_input').val()) {
              if (SEARCH_URL == "/api/profiles/") {
                  // updated url to work with new autocomplete backend format
                  // a user profile has no title; if search was triggered from
                  // the /people page, filter by username instead
                  var query_key = 'username__icontains';
                  $scope.query[query_key] = $('#text_search_input').val();
              } else if (SEARCH_URL == "/api/groupcategory/") {
                  // Adding in this conditional since both groups autocomplete and searches requests need to search name not title.
                  var query_key = 'name__icontains';
                  $scope.query[query_key] = $('#text_search_input').val();
              } else if (SEARCH_URL == "/api/group_profile/") {
                  // Adding in this conditional since both groups autocomplete and searches requests need to search name not title.
                  $scope.query['title__icontains'] = $('#text_search_input').val();
                  $scope.query['description__icontains'] = $('#text_search_input').val();
                  $scope.query['f_method'] = 'or';
              } else if (SEARCH_URL == "/api/base/") {
                  $scope.query['title__icontains'] = $('#text_search_input').val();
                  $scope.query['abstract__icontains'] = $('#text_search_input').val();
                  $scope.query['keywords__slug__in'] = $('#text_search_input').val();
                  $scope.query['purpose__icontains'] = $('#text_search_input').val();
                  $scope.query['data_description__icontains'] = $('#text_search_input').val();
                  $scope.query['f_method'] = 'or';
              }
            } else {
                reset_query();
            }
            $scope.infiniteScrollLoaded = true;
            $scope.init = true;
            query_api($scope.query);
        }

        function reset_query() {
          if (HAYSTACK_SEARCH) {
              $scope.query['q'] = $('#text_search_input').val('');
          }
          $('.selectpicker').selectpicker('val', '');
          $('.selectpicker').selectpicker('refresh');
          
          $scope.query = {};
          $scope.offset = 0;
          $scope.infiniteScroll = 0;
          $scope.infiniteScrollLoaded = true;
          $scope.filter = false;
          $scope.init = true;
          $location.search($scope.query);

          return query_api($scope.query);
        }

        $('.delete_search_query').on('click', function(e) {
            reset_query();
            // remove active class elements from sidebar
            $(".scrollbar-sidebar a").removeClass("active");
            $("#text_search_input").val('');
            $(".result-wrapper").css('display', 'none');
            $(".input-highlight").css("width", '0em');
        });

        $("#dltDate1").on('click', function (e) {
            reset_query();
            $("#inpDate1").val('');
        });

        $("#dltDate2").on('click', function (e) {
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

})();