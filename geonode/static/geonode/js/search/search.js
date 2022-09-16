'use strict';

(function() {

    var formHandlerMsg = `
      <div id="datasetToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
        <div class="toast-message alert-error align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="toast-header">
            <strong class="mr-auto">Invalid Form</strong>
            <small class="text-muted"></small>
            <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('datasetToast').remove()" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="toast-body">
            <span class="font-lg-1"><strong>File Name</strong> may not be blank.</span>
          </div>
        </div>
      </div>
    `

    var handlerSubmitMsg = `
      <div id="datasetToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
        <div class="toast-message alert-error align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="toast-header">
            <strong class="mr-auto">Upload Dataset</strong>
            <small class="text-muted"></small>
            <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('datasetToast').remove()" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="toast-body">
            <span class="font-lg-1">Please provide either file or external url.</span>
          </div>
        </div>
      </div>
    `
    var deleteAllFilesMsg = `
      <div id="datasetToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
        <div class="toast-message alert-error align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="toast-header">
            <strong class="mr-auto">Delete Files</strong>
            <small class="text-muted"></small>
            <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('datasetToast').remove()" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="toast-body">
            <span class="font-lg-1">Your files has been deleted.</span>
          </div>
        </div>
      </div>
    `

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

    var deleteMsg = `
      <div id="datasetToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
        <div class="toast-message alert-error align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="toast-header">
            <strong class="mr-auto">Delete File</strong>
            <small class="text-muted"></small>
            <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('datasetToast').remove()" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="toast-body">
            <span class="font-lg-1">Your selected file has been deleted.</span>
          </div>
        </div>
      </div>
    `

    var unresolvedFileMsg = `
      <div id="datasetToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
        <div class="toast-message alert-warning align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
          <div class="toast-header">
            <strong class="mr-auto">Resume Upload</strong>
            <small class="text-muted"></small>
            <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('datasetToast').remove()" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="toast-body">
            <span class="font-lg-1">You have unresolved files to upload.</span>
          </div>
        </div>
      </div>
    `

    // hide the autocomplete div results whenever the users click on container
    $('.container').on('click', function(){
        $('.ac-results').addClass("d-none");
    });

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
     * Bind an event to load infinite to display user content
     */
    module.directive("infiniteuserScrollDirective", function() {
        return function(scope, elm, attr) {
          if (scope.infiniteScrollLoaded)
              $(window).on('scroll', function() {
                  if ($(window).scrollTop() + $(window).height() == $(document).height()) {
                      setTimeout(function() {
                          scope.$apply(attr.infiniteuserScrollDirective);
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
    module.controller('geonode_search_controller', function($injector, $scope, $rootScope, $location, $http, $uibModal, Configs) {
        // dataset controller for upload and retrieve all resources detail; too lazy to separate this controller
        var url = $location.absUrl().split('/');
        if (url[url.length - 1] === 'replace') {
            $scope.edit_dataset_id = url[url.length - 2];
        }
        $scope.preview_file = function(ext, id, type) {
            // set global variable then alter once the preview modal is clicked
            var previewModal = $(".preview-file").data('target');
            if ($("#render_file").length) {
                $("#render_file").remove();
            };
            $(previewModal).on('show.bs.modal', function(){
            }).modal('show');
            var preview;
            var download_url = siteUrl + "datasets/upload/file/preview/" + id;
            if (type == 'word' || type == 'excel' || type == 'powerpoint' || ext == 'pdf') {
                preview = "https://docs.google.com/gview?url=" + download_url + "&embedded=true";
            } else {
                preview = download_url;
            }
            module.render_file(ext, type, preview, id);
        }

        $scope.post_file = function (dataset_id) {
          $('#submit').prop("disabled", true)
          setTimeout(function() {
            $('#submit').prop("disabled", false)
          }, 2000);

          var file = $("#doc_file").val();
          var file_url = $("#id_file_url").val();
          if (file || file_url) {
              var uploader = module.upload_dataset_file($http, $rootScope, document.querySelector('#doc_file'), dataset_id);
          } else {
              $(document.body).append(handlerSubmitMsg);
              setTimeout(function() {
                $('#datasetToast').remove();
              }, 4000)
          }
        };

        $scope.delete_file = function(id) {
            var deleteParams = {
                method: 'DELETE',
                data: {pk: id},
                url: siteUrl + "api/v2/files/delete_file",
                headers: {
                    'Content-type': 'application/json;charset=utf-8'
                }
            };
            $http(deleteParams).then(successCallback)

            function successCallback(res) {
                $rootScope.datasets = $rootScope.datasets.filter(file => file.id !== id);
                $(document.body).append(deleteMsg);
                setTimeout(function() {
                    $("#datasetToast").remove();
                }, 3000);
                setTimeout(function() {
                  $("#card-"+id+"").remove();
                  if ($rootScope.datasets.length < 1) {
                      $(".card-ingest").addClass('d-none');
                  }
                }, 1500)
            };

        };

        $scope.upload_datasets = function($event) {
            var perms_form = $("#permission_form");
            var perms;
            if (perms_form.length) {
                $('#permissions').val(JSON.stringify(perms_form.serializeObject()));
                perms = $('#permissions').val();
            }

            function patchDatasetFile() {
                var datasets_files = new Array();
                for (var i = 0; i < $rootScope.datasets.length; i++) {
                    if (!$(".file_name:eq("+i+")").val()) {
                        $(document.body).append(formHandlerMsg)
                        setTimeout(function() {
                          $('#datasetToast').remove();
                        }, 2500)
                    }
                    datasets_files.push({
                        "id": $(".file_id:eq("+i+")").val(),
                        "file_name": $(".file_name:eq("+i+")").val(),
                        "file_url": $(".file_url:eq("+i+")").val(),
                        "file_description": $(".file_description:eq("+i+")").val(),
                        "file_data_quality": $(".file_data_quality:eq("+i+")").val(),
                        "permissions": perms
                        // "file_keywords": $(".file_keywords:eq("+i+")").val(),
                    })
                }
                return datasets_files
            }

            function patchReplaceDatasetFile() {
                var datasets_files = new Array();
                for (var i = 0; i < $rootScope.datasets.length; i++) {
                    if (!$(".file_name:eq("+i+")").val()) {
                        $(document.body).append(formHandlerMsg)
                        setTimeout(function() {
                          $('#datasetToast').remove();
                        }, 2500)
                    }
                    datasets_files.push({
                        "id": $(".file_id:eq("+i+")").val(),
                        "file_name": $(".file_name:eq("+i+")").val(),
                        "file_url": $(".file_url:eq("+i+")").val(),
                        "file_description": $(".file_description:eq("+i+")").val(),
                        "file_data_quality": $(".file_data_quality:eq("+i+")").val()
                        // "file_keywords": $(".file_keywords:eq("+i+")").val(),
                    })
                }
                return datasets_files
            }

            if ($scope.edit_dataset_id) {
                var postParams = {
                    method: 'PATCH',
                    url: siteUrl + "api/v2/files/patch_dataset_files/" + $scope.edit_dataset_id,
                    transformRequest: angular.identity,
                    data: JSON.stringify(patchReplaceDatasetFile()),
                    cache: false,
                    dataType: 'json',
                    headers: {'Content-Type': "application/json" }
                };
            } else {
              var postParams = {
                  method: 'PATCH',
                  url: siteUrl + "api/v2/files/upload_dataset_files",
                  transformRequest: angular.identity,
                  data: JSON.stringify(patchDatasetFile()),
                  cache: false,
                  dataType: 'json',
                  headers: {'Content-Type': "application/json" }
              };
            }

            $('.btn-upload').prop("disabled", true);
            setTimeout(function() {
                $('.btn-upload').prop("disabled", false);
            }, 1000);

            $http(postParams).then(successCallback);

            function successCallback(data) {
                var _siteUrl = siteUrl.slice(0, -1);
                var redirect_url = data.data.response;
                setTimeout(function(){location.href=_siteUrl + redirect_url}, 5e2);
            }
        };

        $scope.remove_ui_modal = function() {
            $(".datasetVersionModal").remove();
            $(".modal-backdrop").remove();
            $("body").removeClass('modal-open');
        }

        $scope.load_version_changes = function($http, API_CHANGE_VERSION) {
          $http.get(API_CHANGE_VERSION).then(successCallback)
          function successCallback(data) {
              var _data = data.data.objects;
              $scope.version_changes = _data;
              var modalInstance = $uibModal.open({
                  templateUrl: staticUrl + "geonode/js/templates/modal/version_detail.html",
                  scope: $scope,
                  size: 'lg',
                  windowClass: 'datasetVersionModal',
              });
              setTimeout(function() {
                  $(".datasetVersionModal").modal('show');
              }, 500);
              modalInstance.result.then(closedCallback, dismissedCallback);
              function closedCallback(){
                // Do something when the modal is closed
                console.log("Close ui angular modal");
              }

              function dismissedCallback(){
                // Do something when the modal is dismissed
                  $(".datasetVersionModal").remove();
                  $(".modal-backdrop").remove();
                  $("body").removeClass('modal-open');
              }
          }
        }

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
                    if ($location.path().includes("catalogue") || $location.path() == "/people/" || $location.path().includes("groups")) {
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
            $(".result-wrapper").css('display', 'none');
            $(".input-highlight").css("width", '0em');
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

        $('.delete_search_query').on('click', function(e) {
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

        $scope.add_to_favorite = function(resource_id, is_favorited) {
          var favoriteMsg = (status, msg) => {
              return `
              <div id="favoriteToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
                <div class="toast-message alert-`+status+` align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
                  <div class="toast-body">
                    <span class="font-lg-1">`+msg+`</span>
                    <button type="button" class="close pl-2" style="font-size: .9em" aria-label="Close" onclick="document.getElementById('favoriteToast').remove()">
                      <i class="fa-solid fa-xmark"></i>
                    </button>
                  </div>
                </div>
              </div>
            `
          }
          if (!is_favorited) {
              var postParams = {
                method: 'POST',
                data: {pk: resource_id},
                url: siteUrl + "api/v2/resources/"+resource_id+"/favorite",
                headers: {
                    'Content-type': 'application/json;charset=utf-8'
                }
              };
              $("#add-favorite-"+resource_id+"").html('<i class="fa-solid fa-star" title="Just added to your favorites"></i>')
          } else {
              var postParams = {
                method: 'DELETE',
                type: 'DELETE',
                data: {pk: resource_id},
                url: siteUrl + "api/v2/resources/"+resource_id+"/favorite",
                headers: {
                    'Content-type': 'application/json;charset=utf-8'
                }
              };
              $("#add-favorite-"+resource_id+"").html('<i class="fa-regular fa-star" title="Just removed from your favorites"></i>')
          }

          $http(postParams).then(successCallback, errorCallback)

          function successCallback(res) {
              var msg = res.data.message;
              $(document.body).append(favoriteMsg('success', msg));
              setTimeout(function() {
                $('#favoriteToast').remove();
              }, 3000)
          }

          function errorCallback(res) {
              var msg = res.data.message;
              $(document.body).append(favoriteMsg('error', msg));
              setTimeout(function() {
                $('#favoriteToast').remove();
              }, 3000)
          }
        }

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

    module.filter ('stripHTML', [function () {
      return function (stringWithHtml) {
          if (typeof(stringWithHtml) != 'object') {
              var strippedText =  $('<div/>').html(stringWithHtml).text();
          } else {
              var strippedText = stringWithHtml.join(', ');
          }
          return strippedText;
      };
    }]);

    module.upload_dataset_file = function($http, $rootScope, file, dataset_id) {
      // https://github.com/shubhamkshatriya25/AJAX-File-Uploader/blob/master/static/js/app.js
      const max_length = 1024 * 1024 * 10;
    
      const clearInputFile = () => {
          $("#doc_file").val('');
          $("#id_file_url").val('');
          if ($('.files_selected').length) {
              $('.files_selected').remove();
              $('#drop-zone').removeClass('drop-selected');
          }
      }

      function create_progress_bar() {
          var progress = `
            <div class="col-md-12 mt-2 uploaded_files">
              <div class="card">
                <div class="card-body">
                  <div class="row">
                    <div class="d-flex flex-row pl-4">
                      <svg width="40" height="50" viewBox="0 0 40 50" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M1.02553 0.0995904C0.882016 0.158264 0.656338 0.29551 0.533629 0.413368C-0.0404368 0.923066 0.000643972 -0.772868 0.000643972 25.0253V48.8918L0.226322 49.2153C0.359702 49.3918 0.595517 49.6367 0.74917 49.7449C1.0362 49.9505 1.05701 49.9505 11.2387 49.9505H21.4305L21.7074 49.676C21.9843 49.4209 21.9944 49.3719 21.9944 48.4209V47.4306L21.6561 47.1464L21.328 46.8622H12.3046H3.28125V24.9957V3.1292H14.0989H24.9165V7.95373C24.9165 11.1308 24.9576 12.9252 25.0296 13.1798C25.0909 13.3956 25.2654 13.6997 25.4089 13.8563C25.9526 14.4053 25.9008 14.4053 31.5305 14.4053H36.7083V21.9074C36.7083 30.2422 36.6774 29.8697 37.3747 30.1539C37.826 30.3304 38.8717 30.3304 39.3124 30.1539C40.0401 29.8697 39.9889 30.4973 39.9889 20.9957C39.9889 12.7298 39.9788 12.4257 39.7942 12.0726C39.497 11.5334 27.726 0.335301 27.2544 0.139381C26.9161 0.0118286 25.378 -0.00755636 14.0786 0.0021376C5.83467 0.00162739 1.18986 0.0409164 1.02553 0.0995904ZM31.3758 8.37568L34.4008 11.2686H31.3454H28.3001V8.37568C28.3001 6.7874 28.3102 5.4828 28.331 5.4828C28.3406 5.4828 29.7149 6.7874 31.3758 8.37568Z" fill="black"/>
                      <path d="M26.6285 34.0856C24.4342 36.1841 22.5066 38.0861 22.3428 38.3213C21.502 39.5565 22.64 41.0571 24.1269 40.6846C24.4961 40.5867 24.8957 40.2433 26.9156 38.3213C28.2179 37.0856 29.3148 36.0759 29.3559 36.0759C29.3868 36.0759 29.4381 38.9979 29.4482 42.5673C29.4791 48.8918 29.4893 49.0781 29.684 49.3332C29.9401 49.6765 30.6171 50 31.0578 50C31.5396 50 32.1446 49.6663 32.4113 49.2449L32.6573 48.8724L32.6882 42.4596L32.7192 36.0371L35.0981 38.3019C37.1693 40.2826 37.5385 40.5867 37.9386 40.6846C39.282 41.028 40.4403 39.704 39.8353 38.4882C39.7531 38.3213 37.8255 36.4096 35.5495 34.2325C31.5092 30.3794 31.4169 30.2912 31.0167 30.2912C30.6166 30.2912 30.5248 30.3794 26.6285 34.0856Z" fill="black"/>
                      </svg>
                    </div>
                    <div class="col">
                        <p class="filename"></p>
                        <div class="progress mt-1">
                            <div class="progress-bar bg-info" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%">
                            </div>
                        </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          `
          $("#body_inner").append(progress);
      }

      function upload() {
          create_progress_bar();
          initFileUpload(file);
      }

      function initFileUpload() {
          file = file.files[0];
          upload_file(0, null);
      }

      function upload_file(start, model_id) {
          var end;
          var self = this;
          var existingPath = model_id;
          var formData = new FormData();
          var nextChunk = start + max_length + 1;
          $.ajaxSetup({
              headers: {
                  "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
              }
          });
          formData.append('file_url', $('#id_file_url').val());
          formData.append('import_id', $('#import_id').val());
          if (dataset_id) {
              formData.append('dataset_id', dataset_id);
          }

          if (file) {
              var currentChunk = file.slice(start, nextChunk);
              var uploadedChunk = start + currentChunk.size;
              var file_name = file.name;
              var file_size = file.size;
              var extension = file_name.substring(file_name.lastIndexOf('.') + 1);
              if (uploadedChunk >= file.size) {
                  end = 1;
              } else {
                  end = 0;
              }
              formData.append('file', currentChunk);
              formData.append('file_name', file_name);
              formData.append('file_size', file_size);
              formData.append('extension', extension);
              formData.append('end', end);
              formData.append('existingPath', existingPath);
              formData.append('nextSlice', nextChunk);
              $('.filename').text(file.name);
              var postParams = {
                  method: 'POST',
                  url: siteUrl + "datasets/upload/file",
                  transformRequest: angular.identity,
                  uploadEventHandlers: {
                      progress: function (e) {
                                if (e.lengthComputable) {
                                  if (file.size < max_length) {
                                      var pct = Math.round((e.loaded / e.total) * 100);
                                  } else {
                                      var pct = Math.round((uploadedChunk / file.size) * 100);
                                  }
                                  $('.progress-bar').css('width', pct + '%');
                                  $('.progress-bar').text(pct + '%');
                                }
                      }
                  },
                  data: formData,
                  headers: {'Content-Type': undefined }
              };
          } else {
              var postParams = {
                  method: 'POST',
                  url: siteUrl + "datasets/upload/file",
                  data: formData,
                  cache: false,
                  dataType: 'json',
                  headers: {'Content-Type': undefined }
              };
          }
          var uploadFile = $http(postParams).then(function(res) {
              var _data = res.data.objects;
              var is_external_data = _data.file_url;
              $rootScope.datasets.push(_data);
              var datasets_id = []
              $rootScope.datasets.map(o => ( datasets_id.push(o.id)));
              window.localStorage.setItem('file_ids', JSON.stringify(datasets_id))
              if (!is_external_data) {
                  setTimeout(function() {
                    $(".uploaded_files").remove();
                    if ($(".card-ingest").hasClass('d-none')) {
                      $(".card-ingest").removeClass('d-none');
                    }
                    clearInputFile();
                }, 2000);
              } else {
                  $(".uploaded_files").remove();
                  if ($(".card-ingest").hasClass('d-none')) {
                    $(".card-ingest").removeClass('d-none');
                  }
                  clearInputFile();
              }
          });
      };
      return upload();
    }

    module.renderPDFFile = function(dataset_file_id) {
      // ref https://mozilla.github.io/pdf.js/examples/index.html#interactive-examples
      var url = siteUrl + "datasets/upload/file/preview/" + dataset_file_id;
      var pdfDoc = null,
          pageNum = 1,
          pageRendering = false,
          pageNumPending = null,
          zoom = 1,
          scale = 0.8,
          canvas = document.getElementById('pdf_renderer'),
          ctx = canvas.getContext('2d');

      /**
        * Get page info from document, resize canvas accordingly, and render page.
        * @param num Page number.
        */
      function renderPage(num) {
          pageRendering = true;
          // Using promise to fetch the page
          pdfDoc.getPage(num).then(function(page) {
              var viewport = page.getViewport({scale: scale});
              canvas.height = viewport.height;
              canvas.width = viewport.width;

              // Render PDF page into canvas context
              var renderContext = {
                  canvasContext: ctx,
                  viewport: viewport
              };
              var renderTask = page.render(renderContext);

              // Wait for rendering to finish
              renderTask.promise.then(function() {
                  pageRendering = false;
                  if (pageNumPending !== null) {
                      // New page rendering is pending
                      renderPage(pageNumPending);
                      pageNumPending = null;
                  }
              });
          });

          // Update page counters
          document.getElementById('current_page').value = num;
      }

      /**
        * If another page rendering in progress, waits until the rendering is
        * finised. Otherwise, executes rendering immediately.
        */
      function queueRenderPage(num) {
          if (pageRendering) {
              pageNumPending = num;
          } else {
              renderPage(num);
          }
      }

      /**
        * Jump to page.
        */
      function onJumpPage() {
        if (pdfDoc == null) return;
        
        var e = window.event;
        var code = (e.keyCode ? e.keyCode : e.which);

        // check if key code matches the Enter key
        if(code == 13) {
          var desiredPage = $("#current_page").val();
          if(desiredPage >= 1 && desiredPage <= pdfDoc.numPages) {
              pageNum = parseInt(desiredPage);
              queueRenderPage(pageNum)
              document.getElementById("current_page").value = desiredPage;
          }
        }
      }
      document.getElementById('current_page').addEventListener('keypress', onJumpPage);

      /**
        * Displays previous page.
        */
      function onPrevPage() {
          if (pageNum <= 1) {
              return;
          }
          pageNum--;
          queueRenderPage(pageNum);
      }
      document.getElementById('prev').addEventListener('click', onPrevPage);

      /**
        * Displays next page.
        */
      function onNextPage() {
        if (pageNum >= pdfDoc.numPages) {
          return;
        }
        pageNum++;
        queueRenderPage(pageNum);
      }
      document.getElementById('next').addEventListener('click', onNextPage);

      /**
        * Zoom in PDF.
        */
      function zoomIn() {
          if(pdfDoc == null) return;

          scale += zoom;
          var num = parseInt($("#current_page").val());
          console.log("scale ", scale, "num ", num, "pageRendering ", pageRendering)
          
          queueRenderPage(num);
      }
      // document.getElementById('zoom_in').addEventListener('click', zoomIn);


      /**
        * Zoom out PDF.
        */
        function zoomOut() {
          if(pdfDoc == null) return;

          scale -= 0.5;
          var num = parseInt($("#current_page").val());
          queueRenderPage(num);
      }
      // document.getElementById('zoom_out').addEventListener('click', zoomOut);

      /**
        * Asynchronously downloads PDF.
        */
      pdfjsLib.getDocument(url).promise.then(function(pdfDoc_) {
          pdfDoc = pdfDoc_;
          document.getElementById('page_count').textContent = pdfDoc.numPages;

          // Initial/first page rendering
          renderPage(pageNum);
      });
    }

    module.render_file = function(ext, type, url, id) {
      var render_html;
      if (ext == 'odp') {
          render_html = `
            <canvas id="pdf_renderer" class="w-100"></canvas>
            <div class="row justify-content-center mt-2">
                <div id="prev" class="btn btn-light mr-4"><i class="fa-solid fa-angle-left"></i></div>
                <div>
                  <input id="current_page" value="1" type="text" class="btn btn-light text-center mr-3" style="width: 60px; border: 1px solid var(--shadow-1) !important;">
                  <span> / <span id="page_count"></span> </span>
                </div>
                <div id="next" class="btn btn-light ml-4"><i class="fa-solid fa-angle-right"></i></div>
            </div>
          `
      }
      else if (type == 'word' || type == 'excel' || type == 'powerpoint' || ext == 'pdf') {
          render_html = '<iframe src='+ url +' width="100%" height="480px" frameborder="0"></iframe>'
      }
      else if (type == 'image') {
          render_html = '<img src='+ url +' width="100%" class="img-responsive" />'
      }
      else if (type == 'text') {
            $.ajax({
              url: url,
              type: 'GET',
              success: function(data) {
                $('#text_container').append(data);
              }
          });
          render_html = '<pre id="text_container" class="bg-light p-0 m-0"></pre>'
      }
      else if (type == 'tabular') {
            var loading = '<div class="spinner-grow text-info mr-3 d-inline-flex" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div> \
            <div class="spinner-grow text-info" role="status"><span class="sr-only text-center">Loading...</span></div>';
            $.ajax({
              url: url,
              type: 'GET',
              success: function(data) {
                $('#dataframe_container').append(data);
                $("#tabular_data").DataTable({
                  scrollY:        "600px",
                  scrollX:        true,
                  scrollCollapse: true,
                  paging:         true
                });
                $("#previewDatasetFiles .modal-title").html("Preview File <span class='text-muted small' id='tabular'>(limited to 1000 data)</span>")
              },
              beforeSend: function() {
                $('#dataframe_container').append(loading);
              },
              complete: function() {
                $('.spinner-grow').remove();
              }
          });
          render_html = '<div class="p-3 bg-light" id="dataframe_container"></div>'
      }
      else if (type == 'video') {
          render_html = `
            <video width="500" controls>
              <source src="`+url+`">
              Your browser does not support the video tag.
            </video>
          `
      }
      else {
          render_html = '<p>We have a trouble for previewing your file, please download <a href='+url+' target="_blank">here</a></p>'
      }        
      $("#preview_file").append('<div id="render_file">'+render_html+'</div>');
      if (!type == 'tabular') {
          $("#previewDatasetFiles .modal-title").html("Preview File")
          $("#tabular").remove();
      }
      if ($("#pdf_renderer").length) {
          module.renderPDFFile(id);
      }
    }

    module.load_dataset_version = function($http, $rootScope, scope, API_DATASET_VERSION, dataset_id) {
      $http.get(API_DATASET_VERSION).then(successCallback);

      function successCallback(data) {
          var _data = data.data.objects;
          if (_data.length == 0) {
              console.log("No version")
          } else {
            setTimeout(function() {
                if (_data.length > 10) {
                    var table = $("#versions_table").DataTable({
                      scrollCollapse: true,
                      paging:         true,
                      info:           false
                    });
                } else {
                    var table = $("#versions_table").DataTable({
                      scrollCollapse: true,
                      paging:         false,
                      info:           false
                    });
                };
                $('#versions_table tbody').on('click', 'tr', function () {
                    var data = table.row(this).data();
                    var version = data[0];
                    if (dataset_id.includes("_")) {
                        // api for layers
                        var API_CHANGE_VERSION = siteUrl + "api/v2/versions/get_detailed_version?l=" + dataset_id + "&v=" + version;
                    } else {
                        // api for datasets
                        var API_CHANGE_VERSION = siteUrl + "api/v2/versions/get_detailed_version?d=" + dataset_id + "&v=" + version;
                    }
                    scope.load_version_changes($http, API_CHANGE_VERSION);
                });
            }, 1000);
          }
          $rootScope.versions = _data;
      }
    }

    module.load_resume_upload = function($http, $rootScope) {
      $http.get(siteUrl + "api/v2/files/resume_upload").then(successCallback);

      function successCallback(data) {
          $rootScope.datasets = data.data.objects;
          var datasets_id = []
          if ($rootScope.datasets.length > 0) {
              if ($(".card-ingest").hasClass('d-none')) {
                $(".card-ingest").removeClass('d-none');
              }
              $(document.body).append(unresolvedFileMsg);
              setTimeout(function() {
                  $('#datasetToast').remove();
              }, 4000)
              $rootScope.datasets.map(o => ( datasets_id.push(o.id)));
              window.localStorage.setItem('file_ids', JSON.stringify(datasets_id))
          }
      }
    }

    module.edit_dataset_files = function($http, $rootScope, dataset_id) {
      $http.get(siteUrl + "api/v2/files/edit_dataset_files/" + dataset_id).then(successCallback);

      function successCallback(data) {
          $rootScope.datasets = data.data.objects;
          var datasets_id = []
          if ($rootScope.datasets.length > 0) {
              if ($(".card-ingest").hasClass('d-none')) {
                $(".card-ingest").removeClass('d-none');
              }
              $rootScope.datasets.map(o => ( datasets_id.push(o.id)));
              window.localStorage.setItem('file_ids', JSON.stringify(datasets_id))
          }
      }
    }

    module.directive("dropzone", function($http, $rootScope, $location) {
        return {
            restrict : "A",
            link: function (scope, elem) {
                var url = $location.absUrl().split('/');
                var dataset_id;
                if (url[url.length - 1] === 'replace') {
                    dataset_id = url[url.length - 2];
                } else {
                    dataset_id = null;
                }

                elem.on('drop', function(evt) {
                    evt.stopPropagation();
                    evt.preventDefault();
                    const files = evt.originalEvent.dataTransfer;
                    var uploader = module.upload_dataset_file($http, $rootScope, files, dataset_id);
                });
                elem.on('dragenter', function(evt) {
                    evt.preventDefault();
                    evt.stopPropagation();
                });
                elem.on('dragover', function(evt) {
                  evt.preventDefault();
                  evt.stopPropagation();
                });
                elem.on('dragleave', function(evt) {
                  evt.preventDefault();
                  evt.stopPropagation();
                });
            }
        }
    })

    module.directive("cardingest", function($http, $rootScope, $location) {
        return {
            restrict: "A",
            link: function(scope, elem) {
                var url = $location.absUrl().split('/');
                var dataset_id = url[url.length - 2];
                if (url[url.length - 1] === 'replace') {
                    module.edit_dataset_files($http, $rootScope, dataset_id)
                } else {
                    module.load_resume_upload($http, $rootScope);
                }
            },
            templateUrl: staticUrl + "geonode/js/templates/card_ingest.html"
        }
    })

    module.directive("datasetversion", function($http, $rootScope, $location) {
      return {
          restrict: "A",
          link: function(scope, elem) {
              var url = $location.absUrl().split('/');
              var dataset_id = url[url.length - 1];
              if (dataset_id.includes("_")) {
                  // api for layers
                  var API_DATASET_VERSION = siteUrl + "api/v2/versions?l=" + dataset_id + "&all";
              } else {
                  // api for datasets
                  var API_DATASET_VERSION = siteUrl + "api/v2/versions?d=" + dataset_id + "&all";
              }
              module.load_dataset_version($http, $rootScope, scope, API_DATASET_VERSION, dataset_id);
          },
          templateUrl: staticUrl + "geonode/js/templates/dataset_version.html"
      }
    })

})();