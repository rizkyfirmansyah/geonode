'use strict';

(function() {
    angular.module('cart', ['ngCookies'])

    .filter('title', function() {
        return function(value) {
            return value.replace(/\w\S*/g, function(txt) { return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase(); });
        };
    })

    .filter('default_if_blank', function() {
        return function(value, arg) {
            return angular.isString(value) && value.length > 0 ? value : arg;
        };
    })

    .filter('limitWithEllipsis', function() {
        return function(input, limit, begin) {
            var str='';
              if (Math.abs(Number(limit)) === Infinity) {
                limit = Number(limit);
              } else {
                limit = parseInt(limit);
              }
              if (isNaN(limit)) return input;

              if (angular.isNumber(input)) input = input.toString();
              if (!angular.isArray(input) && !angular.isString(input)) return input;
              if(input.length<=limit) return input;
              begin = (!begin || isNaN(begin)) ? 0 : parseInt(begin);
              begin = (begin < 0) ? Math.max(0, input.length + begin) : begin;

              if (limit >= 0) {
                str=input.slice(begin, begin + limit);
                return str.concat('....'); 
              } else {
                if (begin === 0) {
                  str=input.slice(limit, input.length);
                  return str.concat('....');
                } else {
                  str=input.slice(Math.max(0, begin + limit), begin);
                  return str.concat('....');
                }
              }
          };
    })

    .controller('CartList', function($scope, cart, $http, $window) {
        $scope.cart = cart;
        $scope.layers_params = '';

        $scope.newMap = function() {
            var items = cart.getCart().items;
            var params = '';
            for (var i = 0; i < items.length; i++) {
                params += 'layer=' + items[i].detail_url.split('/')[2] + '&';
            }
            window.location = siteUrl + 'maps/new?' + params;
        }

        $scope.securityRefreshButton = function($event) {
            $event.preventDefault();
            sessionStorage.setItem("security_refresh_trigger", true);
            window.location.href = $event.target.href;
        };

        $scope.bulk_perms_submit = function() {
            var items = cart.getCart().items;
            var selected_ids = $.map(items, function(item) { return item.pk });
            var data = $("#bulk_permission_form").serializeObject();
            var message = $('#bulk_perms_message');
            if (selected_ids.length == 0) {
                message.find('.message').html('Please select at least one resource to set the permissions');
                message.addClass('alert-danger').removeClass('alert-success alert-warning hidden');
                return;
            }
            var bulkPermsMsg = function(msg, status = 'success') {
                return `
                <div id="permsToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
                  <div class="toast-message alert-`+status+` align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-header">
                      <strong class="mr-auto">Set Permissions</strong>
                      <small class="text-muted"></small>
                      <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('permsToast').remove()" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                      </button>
                    </div>
                    <div class="toast-body">
                      <span class="font-lg-1">`+msg+`.</span>
                    </div>
                  </div>
                </div>
              `
            }
            var today = new Date();
            var date = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
            var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
            var dateTime = date+' '+time;

            var toastLoadingMsg = function(title, status = 'info') {
                return `
                <div id="loadingToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
                  <div class="toast-message alert-`+status+` align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-header">
                      <strong class="mr-auto">`+title+`</strong>
                      <small class="text-muted">`+time+`</small>
                      <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('loadingToast').remove()" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                      </button>
                    </div>
                    <div class="toast-body">
                        <p class="text-center text-primary" id="remaining">
                          <span class="text-center text-primary">Grab your favourite snack, coffee, or tea while waiting :)</span>
                        </p>
                        <div class="row justify-content-center">
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                        </div>
                    </div>
                  </div>
                </div>
                `
            }
            
            $.ajax({
                type: "POST",
                headers: {"X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value },
                url: siteUrl + "security/bulk-permissions",
                data: {
                    permissions: JSON.stringify(data),
                    resources: JSON.stringify(selected_ids)
                },
                beforeSend: function() {
                    Pace.start();
                    const toast_title = "Updating Permission Resources";
                    $(document.body).append(toastLoadingMsg(toast_title));
                },
                complete: function() {
                    // Handle the complete event
                    $('#loadingToast').remove();
                    try {
                        $("#bulkModalPerms").modal("hide");
                    } catch (err) {
                        console.log(err);
                    }
                },
                success: function(data) {
                    var not_changed = $.parseJSON(data).not_changed;
                    var msg;
                    if (not_changed.length > 0) {
                        msg = 'Permissions correctly registered, although the following resources were' +
                        ' skipped because you don\'t have the rights to edit their permissions:' + not_changed.join('</br>')
                        $(document.body).append(bulkPermsMsg(msg));
                        setTimeout(function() {
                            $("#permsToast").remove();
                        }, 2000);
                    } else {
                        msg = 'Permissions correctly registered.'
                        $(document.body).append(bulkPermsMsg(msg));
                        setTimeout(function() {
                            $("#permsToast").remove();
                        }, 2000);
                    }
                    Pace.stop();
                },
                error: function(data) {
                    msg = $.parseJSON(data).error
                    $(document.body).append(bulkPermsMsg(msg, 'error'));
                    setTimeout(function() {
                        $("#permsToast").remove();
                    }, 2000);
                }
            });
        };

        $scope.bulk_metadata_submit = function($event) {
            var items = cart.getCart().items;
            var selected_ids = $.map(items, function(item) { return item.pk });
            var data = $("#bulk_metadata_form").serializeObject();
            var bulkMetadataMsg = function(msg, status = 'success') {
                return `
                <div id="bulkMetadataToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
                  <div class="toast-message alert-`+status+` align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-header">
                      <strong class="mr-auto">Edit Metadata</strong>
                      <small class="text-muted"></small>
                      <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('bulkMetadataToast').remove()" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                      </button>
                    </div>
                    <div class="toast-body">
                      <span class="font-lg-1">`+msg+`.</span>
                    </div>
                  </div>
                </div>
              `
            }

            var toastLoadingMsg = function(title, status = 'info') {
                return `
                <div id="loadingToast" class="position-fixed bottom-0 right-0 p-3" style="z-index: 99999; right: 0; bottom: 0;">
                  <div class="toast-message alert-`+status+` align-items-center" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-header">
                      <strong class="mr-auto">`+title+`</strong>
                      <small class="text-muted">`+time+`</small>
                      <button type="button" class="ml-2 mb-1 close" onclick="document.getElementById('loadingToast').remove()" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                      </button>
                    </div>
                    <div class="toast-body">
                        <p class="text-center text-primary" id="remaining">
                          <span class="text-center text-primary">Grab your favourite snack, coffee, or tea while waiting :)</span>
                        </p>
                        <div class="row justify-content-center">
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                          <div class="spinner-grow text-info mr-3" role="status"><span class="sr-only text-center">Loading...</span></div>
                        </div>
                    </div>
                  </div>
                </div>
                `
            }
            
            $.ajax({
                type: "POST",
                headers: {"X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value },
                url: siteUrl + "security/bulk-metadata",
                data: {
                    resources: JSON.stringify(data),
                    ids: JSON.stringify(selected_ids)
                },
                beforeSend: function() {
                    Pace.start();
                    const toast_title = "Updating Metadata Resources";
                    $(document.body).append(toastLoadingMsg(toast_title));
                },
                complete: function() {
                    $('#loadingToast').remove();
                },
                success: function(data) {
                    var msg = 'Metadata has been updated on your selected resources';
                    $(document.body).append(bulkMetadataMsg(msg));
                    setTimeout(function() {
                        $("#bulkMetadataToast").remove();
                        $("#bulkMetadataForm").modal("hide");
                        $window.location.reload();
                        // reset modal
                    }, 1000);
                    Pace.stop();
                },
                error: function(xhr, status, error) {
                    var msg = xhr.responseText;
                    var errors = msg.errors;
                    console.log(errors, msg);
                }
            });
        };

    })

    .directive('resourceCart', ['$sce', function($sce) {
        return {
            restrict: 'EA',
            templateUrl: $sce.trustAsResourceUrl(staticUrl + "geonode/js/templates/cart.html"),
            link: function($scope, $element) {
                // Don't use isolateScope, but add to parent scope
                $scope.facetType = $element.attr("data-facet-type");
                $scope.selectedString = $element.attr("selectedString");
                $scope.emptyString = $element.attr("emptyString");
            }
        };
    }])

    .service('cart', function($cookies) {
        this.init = function() {
            this.$cart = {
                items: this.fillCart(),
            };
        };

        this.fillCart = function() {
            // This will fail if angular<1.4.0
            try {
                var geonodeCart = $cookies.getAll();
            } catch (err) {
                var geonodeCart = null;
            }
            var cartSession = [];
            if (geonodeCart !== null) {
                if (Object.keys(geonodeCart).length > 1) {
                    Object.keys(geonodeCart).forEach(function(key, index) {
                        if (key !== 'csrftoken') {
                            try {
                                var obj = JSON.parse(geonodeCart[key]);
                                if (!Number.isInteger(obj)) {
                                    obj.$$hashKey = "object:" + index;
                                    if ('alternate' in obj) {
                                        cartSession.push(obj);
                                    }
                                }
                            } catch (err) {
                                // console.log("Cart Session Issue: " + err.message);
                            }
                        }
                    });
                }
            }
            return cartSession;
        };

        this.getCart = function() {
            return this.$cart;
        }

        this.addItem = function(item) {
            if (!item.pk && item.layer_identifier) {
                item.pk = item.layer_identifier;
            }

            if (this.getItemById(item.pk) === null) {
                this.getCart().items.push(item);
                var cookie_item = {};
                cookie_item['pk'] = item.pk
                cookie_item['detail_url'] = item.detail_url
                $cookies.putObject(item['uuid'], cookie_item);
            }
        }

        this.removeItem = function(item) {
            if (this.getItemById(item.pk) !== null) {
                var cart = this.getCart();
                angular.forEach(cart.items, function(cart_item, index) {
                    if (cart_item.pk === item.pk) {
                        cart.items.splice(index, 1);
                        $cookies.remove(cart_item['uuid']);
                    }
                });
            }
        }

        this.removeAll = function() {
            return this.getCart().items.splice(0);
        }

        this.toggleItem = function(item) {
            if (!$("body").hasClass('show-sidebar-right')) {
                $('body').toggleClass('show-sidebar-right');
            }
            if (this.getItemById(item.pk) === null) {
                this.addItem(item);
            } else {
                this.removeItem(item);
            }
        }

        this.getItemById = function(itemId) {
          var items = this.getCart().items;
            var the_item = null;
            angular.forEach(items, function(item) {
                if (item.pk === itemId) {
                    the_item = item;
                }
            });
            return the_item;
        }

        this.getFaClass = function(id) {
            if (this.getItemById(id) === null) {
                return 'fa-plus';
            } else {
                return 'fa-remove';
            }
        }

        this.category = function(key) {
            const url = siteUrl + 'api/v2/categories/';
            const xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function() {
                if (this.readyState == 4 && this.status == 200) {
                    const response = JSON.parse(xhttp.responseText);
                    response.objects.forEach(function(value, index, array) {
                        if (value.title == key) {
                            const cid = value.identifier;
                            const redirect_to = siteUrl + "catalogue/?f4e493d=" + cid
                            window.location.replace(redirect_to);
                        }
                    })
                }
            };
            xhttp.open("GET", url, true);
            xhttp.send();
        }
    })

    .run(['cart', function(cart) {
        cart.init();
    }])
})();