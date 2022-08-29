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

var dataset = angular.module('dataset', ['ngCookies']);

    dataset.config(['$httpProvider', function($httpProvider) {
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    }]);

    dataset.filter('humanFileSize', function() {
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

    dataset.upload_dataset_file = function($http, $rootScope, file, dataset_id) {
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
              var _data = res.data.files;
              $rootScope.datasets.push(_data);
              var datasets_id = []
              $rootScope.datasets.map(o => ( datasets_id.push(o.id)));
              window.localStorage.setItem('file_ids', JSON.stringify(datasets_id))

              setTimeout(function() {
                  $(".uploaded_files").remove();
                  if ($(".card-ingest").hasClass('d-none')) {
                    $(".card-ingest").removeClass('d-none');
                  }
                  clearInputFile();
              }, 2000);
            });
        };
        return upload();
    }

    dataset.renderPDFFile = function(dataset_file_id) {
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

    dataset.render_file = function(ext, type, url, id) {
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
            dataset.renderPDFFile(id);
        }
    }

    dataset.controller('DatasetList', function($scope, $http, $rootScope, $location) {
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
            dataset.render_file(ext, type, preview, id);
        }

        $scope.post_file = function (dataset_id) {
          $('#submit').prop("disabled", true)
          setTimeout(function() {
            $('#submit').prop("disabled", false)
          }, 2000);

          var file = $("#doc_file").val();
          var file_url = $("#id_file_url").val();
          if (file || file_url) {
              var uploader = dataset.upload_dataset_file($http, $rootScope, document.querySelector('#doc_file'), dataset_id);
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
                url: siteUrl + "api/v2/datasets/delete_file",
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
                    url: siteUrl + "api/v2/datasets/patch_dataset_files/" + $scope.edit_dataset_id,
                    transformRequest: angular.identity,
                    data: JSON.stringify(patchReplaceDatasetFile()),
                    cache: false,
                    dataType: 'json',
                    headers: {'Content-Type': "application/json" }
                };
            } else {
              var postParams = {
                  method: 'PATCH',
                  url: siteUrl + "api/v2/datasets/upload_dataset_files",
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
        }
    })

    dataset.directive("dropzone", function($http, $rootScope, $location) {
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
                    var uploader = dataset.upload_dataset_file($http, $rootScope, files, dataset_id);
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

    dataset.directive("cardingest", function($http, $rootScope, $location) {
        return {
            restrict: "A",
            link: function(scope, elem) {
                var url = $location.absUrl().split('/');
                var dataset_id = url[url.length - 2];
                if (url[url.length - 1] === 'replace') {
                    dataset.edit_dataset_files($http, $rootScope, dataset_id)
                } else {
                    dataset.load_resume_upload($http, $rootScope);
                }
            },
            templateUrl: staticUrl + "geonode/js/templates/card_ingest.html"
        }
    })

    dataset.load_resume_upload = function($http, $rootScope) {
        $http.get(siteUrl + "api/v2/datasets/resume_upload").then(successCallback);

        function successCallback(data) {
            $rootScope.datasets = data.data.files;
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

    dataset.edit_dataset_files = function($http, $rootScope, dataset_id) {
      $http.get(siteUrl + "api/v2/datasets/edit_dataset_files/" + dataset_id).then(successCallback);

      function successCallback(data) {
          $rootScope.datasets = data.data.files;
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

document.getElementById('top').setAttribute('ng-controller', "DatasetList");
angular.bootstrap(document, ['dataset']);
