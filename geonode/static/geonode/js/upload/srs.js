/*globals define: true, requirejs: true */

'use strict';

requirejs.config({
  config: {
     text: {
       useXhr: function (url, protocol, hostname, port) {
          // allow cross-domain requests
          // remote server allows CORS
          return true;
       }
     },
     waitSeconds: 5
  },
  baseUrl: staticUrl + 'lib/js',
  shim: {
    'underscore': { exports: '_'}
  },
  paths: {
    'upload': '../../geonode/js/upload',
    'templates': '../../geonode/js/templates',
    'progress': 'jquery.ajax-progress'
  }
});

define(['upload/upload',
        'upload/common',
        'upload/LayerInfo'], function (upload, common, LayerInfo) {
    'use strict';

    var doSrs = function (event) {
        var form = $("#crsForm");

        function makeRequest(data) {
            common.make_request({
                url: data.redirect_to,
                async: false,
                failure: function (resp, status) {
                    common.logError(resp);
                },
                success: function (resp, status) {
                    if (resp.status) {
                        if (resp.status === 'error') {
                            self.polling = false;
                            common.logError(resp.error_msg);
                        } else if (resp.status === 'pending') {
                            setTimeout(function() {
                                makeRequest(resp);
                            }, 5000);
                            return;
                        } else if (resp.status === 'incomplete') {
                            if('redirect_to' in resp && resp.redirect_to) {
                                self.polling = false;
                                window.location = resp.redirect_to;
                            } else if ('url' in resp && resp.url) {
                                self.polling = false;
                                window.location = resp.url;
                            } else {
                                common.logError("unexpected response");
                            }
                        } else if (resp.status === 'finished') {
                            self.polling = false;
                            window.location = resp.url;
                        }
                    } else {
                         if('redirect_to' in resp && resp.redirect_to) {
                             makeRequest(resp);
                         } else if ('url' in resp && resp.url) {
                             self.polling = false;
                             window.location = resp.url;
                         } else {
                             common.logError("unexpected response");
                         }
                     }
                }
            });
        };

      var params = common.parseQueryString(document.location.search);
      var handlerLoadingMsg = `
        <div id="layerLoadingToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
          <div class="toast-message alert-info align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
              <strong class="mr-auto">Upload Dataset</strong>
              <small class="text-muted"></small>
              <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('layerLoadingToast').remove()" aria-label="Close">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="toast-body">
              <span class="font-lg-1">We are processing your request. Please wait... and please keep this tab opens.</span>
            </div>
          </div>
        </div>
      `
      var url = siteUrl + 'upload/srs'
      if ('id' in params){
        url = updateUrl(url, 'id', params.id);
      }
        $.ajax({
           type: "POST",
           url: url,
           data: form.serialize(), // serializes the form's elements.
           beforeSend: function() {
              $(document.body).append(handlerLoadingMsg);
            },
           success: function(data)
           {
                setTimeout(function() {
                  $('#layerLoadingToast').remove();
                }, 4000)
               if (data.status) {
                   if (data.status === 'error') {
                       self.polling = false;
                       common.logError(data.error_msg);
                   } else if (data.status === 'pending' ||
                            data.status === 'incomplete') {
                       makeRequest(data);
                   }
               } else {
                    if('redirect_to' in data && data.redirect_to) {
                        makeRequest(data);
                    } else if ('url' in data && data.url) {
                        self.polling = false;
                        window.location = data.url;
                    } else {
                        common.logError("unexpected response");
                    }
                }
           },
           error: function (resp, status) {
                common.logError(resp);
           }
        });
        return false;
    };

    $(function () {
        $("#next").on('click', doSrs);
    });

});
