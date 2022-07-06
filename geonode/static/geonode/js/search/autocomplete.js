/**
 * Function used to add autocomplete to input fields.
 * The new version of autocomplete light seems to have built in support for select using select2
 * but does not support regular input autocomplete.
 * @param {object} options Options object for autocomplete including DOM selectors and url
 */
 var Autocomplete = function(options) {

  // Multiple selectors to make this reusable 
  this.form_btn = options.form_btn
  this.form_submit = options.form_submit
  this.form_selector = options.form_selector
  this.input_selector = options.input_selector
  this.container_selector = options.container_selector

  // Custom url for autocomplete can be set otherwise the constant will be used set in search_scripts.html
  this.url = options.url || AUTOCOMPLETE_URL_RESOURCEBASE

  // Minimum input length which autocomplete will activate
  this.minimum_length = parseInt(options.minimum_length || 1)

  // DOM elements
  this.form_elem = null
  this.query_box = null
  this.status = true
}

Autocomplete.prototype.setup = function() {
  var self = this

  // Gets input box for getting input text and container to add the autocomplete element to
  this.form_elem = $(this.form_selector);
  this.query_box = this.form_elem.find($(this.input_selector));
  this.query_container = this.form_elem.find($(this.container_selector));

  // Watch the input box.
  this.query_box.on('keyup', function() {

      // Gets the input text from the search field
      var query = self.query_box.val();
      self.status = true;

      if (query.length < self.minimum_length) {
          $('.ac-results').remove() // Remove autocomplete when no input
          return false
      }

      self.fetch(query, page = 1, remove = true, appendNew = false);
  })

  // On selecting a result, populate the search field.
  this.form_elem.on('click', '.ac-result', function(ev) {
      self.query_box.val($(this).find('.result-autocomplete').text())
      $('.ac-results').remove()
      if (typeof self.form_btn !== 'undefined') {
          $(self.form_btn).click();
      }
      if (typeof self.form_submit !== 'undefined') {
          $(self.form_submit).submit();
      }
      return false
  })
}

Autocomplete.prototype.fetch = function(query, page, remove, appendNew) {
  var self = this
      // Fetching the autocomplete data from the autocomplete light urls set up on backend
      // Filtered based on the current input
  var end_search = '<div class="result-wrapper bg-secondary"><p class="text-center text-light small">-- end of search -- </p></div>'

  if (self.status)
      $.ajax({
          url: this.url,
          data: {
              'q': query,
              'page': page
          },
          success: function(data) {
              var paginated = data.pagination.more;
              self.show_results(data, remove, paginated, appendNew);
          }
      }).fail(function() {
          $(".ac-results").append(end_search);
          self.status = false;
      })
}

Autocomplete.prototype.show_results = function(data, remove, paginated, appendNew) {
  var self = this;
  // Remove any existing results.
  if (remove) $('.ac-results').remove()

  // Mapping to the item text and limiting results shown to 10 only rather
  // than scrolling. Set removes any duplicates.
  var results = [...new Set(data.results.map(item => item.text))] || []
  var results_detail_url = [...new Set(data.results.map(item => item.detail_url))] || []
  var results_resource_type = [...data.results.map(item => item.resource_type)]

  var results_wrapper = $('<div class="ac-results"></div>');
  var base_elem = $('<div class="result-wrapper"><a href="" title="Click to jump into resource detail" class="ac-result btn-light btn_wrapper"></a></div>');
  var container = this.query_container;

  function constructSearch(detail, data, resource, init=true) {
      var elem = base_elem.clone()
      // Adding each query result to the autocomplete element
      // This should use some form of templating instead.
      var icon;
      if (resource == 'layer') {
          icon = '\
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg" class="float-right"> \
            <path d="M17.4167 2.75H4.58333C3.57081 2.75 2.75 3.57081 2.75 4.58333V17.4167C2.75 18.4292 3.57081 19.25 4.58333 19.25H17.4167C18.4292 19.25 19.25 18.4292 19.25 17.4167V4.58333C19.25 3.57081 18.4292 2.75 17.4167 2.75Z" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/> \
            <path d="M7.7915 9.16675C8.55089 9.16675 9.1665 8.55114 9.1665 7.79175C9.1665 7.03236 8.55089 6.41675 7.7915 6.41675C7.03211 6.41675 6.4165 7.03236 6.4165 7.79175C6.4165 8.55114 7.03211 9.16675 7.7915 9.16675Z" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/> \
            <path d="M19.2502 13.7501L14.6668 9.16675L4.5835 19.2501" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/> \
          </svg>'          
      } else if (resource == 'document') {
          icon = '<i title="'+ resource +'" class="fa-solid fa-file float-right"></i>'
      } else if (resource == 'remote') {
          icon = '<i title="'+ resource +'" class="fa-solid fa-layer-group float-right"></i>'
      } else if (resource == 'geoapp') {
          icon = '<i title="'+ resource +'" class="fa-solid fa-gears float-right"></i>'
      } else {
          icon = '<i title="'+ resource +'" class="fa-solid fa-asterisk float-right"></i>'
      }

      elem.find('.ac-result').attr('onclick', "location.href='" + detail + "';");
      elem.find('.ac-result').attr('href', detail);
      elem.find('.ac-result').append('<span class="result-autocomplete">' + data + '</span>');
      elem.find('.ac-result').append(icon);
      elem.find('.ac-result').addClass("text-" + resource);

      if (init) {
          results_wrapper.append(elem)
      } else {
          container.find('.result-wrapper').last().after(elem);
      }
  }

  function appendElement() {
      if (!results.length > 0) return
      for (var res_offset in results) {
          constructSearch(results_detail_url[res_offset], results[res_offset], results_resource_type[res_offset]);
      }
  }

  function appendNewElement() {
      var newResult = [...new Set(data.results.map(item => item.text))] || []
      var newResult_detail_url = [...new Set(data.results.map(item => item.detail_url))] || []
      var newResult_resource_type = [...data.results.map(item => item.resource_type)]
      if (!newResult.length > 0) return
      for (var res_offset in newResult) {
          constructSearch(newResult_detail_url[res_offset], newResult[res_offset], newResult_resource_type[res_offset], false);
      }
  }

  self.scrollEvent(results_wrapper, paginated);
  appendNewElement();
  if (!appendNew) {
      appendElement();
      this.query_box.after(results_wrapper);
  }
}

Autocomplete.prototype.fixPosition = function(html) {
  this.input.parents().filter(function() {
      return $(this).css('overflow') === 'hidden';
  }).first().css('overflow', 'visible');
  if (this.input.attr('name') !== 'resource-keywords') {
      this.box.insertAfter(this.input).css({
          top: 0,
          left: 0
      });
  } else {
      var pos = $.extend({}, this.input.position(), {
          height: this.input.outerHeight()
      });
      this.box.insertAfter(this.input).css({
          top: pos.top + pos.height,
          left: pos.left
      });
  }
}

Autocomplete.prototype.scrollEvent = function(results_wrapper, paginated) {
  var self = this;
  var query = this.query_box.val();
  var page = 1;

  if (self.status)
      results_wrapper.on('scroll', function() {
          if ($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight && paginated) {
              page++;
              self.fetch(query, page = page, remove = false, appendNew = true);
          }
      })
}