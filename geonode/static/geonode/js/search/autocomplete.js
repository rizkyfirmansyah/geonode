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
      self.query_box.val($(this).text())
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
  var end_search = '<div class="result-wrapper bg-dark"><p class="text-center text-light">-- end of search -- </p></div>'

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

  function appendElement() {
      if (!results.length > 0) return
      for (var res_offset in results) {
          var elem = base_elem.clone()
              // Adding each query result to the autocomplete element
              // This should use some form of templating instead.
          elem.find('.ac-result').attr('onclick', "location.href='"+results_detail_url[res_offset]+"';")
          elem.find('.ac-result').attr('href', results_detail_url[res_offset]);
          elem.find('.ac-result').text(results[res_offset])
          elem.find('.ac-result').addClass("text-" + results_resource_type[res_offset])
          results_wrapper.append(elem)
      }
  }

  function appendNewElement() {
      var newResult = [...new Set(data.results.map(item => item.text))] || []
      var newResult_detail_url = [...new Set(data.results.map(item => item.detail_url))] || []
      var newResult_resource_type = [...data.results.map(item => item.resource_type)]
      if (!newResult.length > 0) return
      for (var res_offset in newResult) {
          var elem = base_elem.clone();
          elem.find('.ac-result').attr('onclick', "location.href='"+newResult_detail_url[res_offset]+"';")
          elem.find('.ac-result').attr('href', newResult_detail_url[res_offset])
          elem.find('.ac-result').text(newResult[res_offset]);
          elem.find('.ac-result').addClass("text-" + newResult_resource_type[res_offset])
          container.find('.result-wrapper').last().after(elem);
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