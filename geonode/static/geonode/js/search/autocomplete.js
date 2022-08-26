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
      } else if (resource == 'dataset') {
          icon = '<i title="'+ resource +'" class="fa-solid fa-file float-right"></i>'
      } else if (resource == 'remote') {
          icon = '<i title="'+ resource +'" class="fa-solid fa-layer-group float-right"></i>'
      } else if (resource == 'dashboard') {
          icon = '<i title="'+ resource +'" class="fa-solid fa-chart-line float-right"></i>'
      } else if (resource == 'geostory') {
          icon = '\
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="float-right"> \
            <path d="M6.0938 2.53125C5.24068 2.63437 4.49068 3.21562 4.16255 4.02187L4.05474 4.28906L4.0313 11.4844L4.00787 18.6797L2.09068 18.7031L0.17349 18.7266L0.0797399 18.8531C-0.00463511 18.9656 -0.0093226 19.0078 0.0328649 19.3453C0.168802 20.3719 0.778177 21.1172 1.71568 21.4078C1.97818 21.4875 2.36255 21.4922 9.63286 21.4922C17.0016 21.4922 17.2829 21.4875 17.5313 21.4031C18.4079 21.1031 18.9657 20.5266 19.1766 19.6922C19.2563 19.3734 19.2657 19.1531 19.2657 17.1047C19.2657 15.5391 19.2516 14.8266 19.2141 14.7469C19.1063 14.5078 18.7313 14.4891 18.6141 14.7141C18.5813 14.775 18.5626 15.5391 18.5626 16.9828C18.5626 18.3422 18.5438 19.2562 18.511 19.4344C18.4079 19.9922 18.0094 20.4797 17.4938 20.6719C17.1235 20.8125 16.5329 20.7937 16.1954 20.625C15.6891 20.3766 15.361 19.8844 15.2672 19.2375C15.1829 18.6375 15.8391 18.7031 9.88599 18.7031H4.73443L4.7438 11.5406L4.75787 4.38281L4.87505 4.14844C4.94068 4.01719 5.08599 3.82031 5.20318 3.70312C5.32037 3.58594 5.52193 3.44062 5.64849 3.375L5.88287 3.25781L12.5251 3.24375L19.1719 3.23437L18.9844 3.49687C18.8813 3.64219 18.7501 3.88125 18.6938 4.02656C18.5907 4.28437 18.586 4.34062 18.5719 6.19687C18.5579 8.06719 18.5579 8.10469 18.6516 8.19844C18.7829 8.32969 19.036 8.32969 19.1532 8.19844C19.2376 8.10469 19.2422 8.00156 19.2563 6.69844L19.2704 5.29687H21.1407C22.9547 5.29687 23.0204 5.29219 23.1094 5.20312C23.2266 5.08594 23.236 4.71094 23.1282 4.29375C22.8797 3.32344 22.0922 2.63437 21.1172 2.53125C20.611 2.475 6.53912 2.47969 6.0938 2.53125ZM21.5907 3.38437C22.0032 3.6 22.3547 4.04531 22.4391 4.45781L22.4672 4.59375H20.8641H19.2657L19.2938 4.4625C19.3407 4.275 19.5235 3.92344 19.6688 3.75469C19.8001 3.59531 20.1094 3.39844 20.3813 3.29531C20.6672 3.19219 21.3001 3.23906 21.5907 3.38437ZM14.6204 19.6547C14.686 19.9641 14.8969 20.4141 15.0657 20.6156L15.1969 20.7656L8.52662 20.7562L1.85162 20.7422L1.59849 20.6016C1.21412 20.3906 0.876615 19.9547 0.768802 19.5281L0.740677 19.4062H7.65005H14.5641L14.6204 19.6547Z" fill="black"/> \
            <path d="M6.46889 6.12656C6.22983 6.21562 6.15014 6.525 6.32827 6.70312C6.41264 6.7875 6.48296 6.79688 7.16264 6.79688C7.81421 6.79688 7.91733 6.7875 7.97827 6.7125C8.16108 6.50625 8.10483 6.22969 7.86108 6.14062C7.71577 6.09375 6.59546 6.07969 6.46889 6.12656Z" fill="black"/> \
            <path d="M9.24859 6.14063C9.03297 6.22969 8.98141 6.52969 9.15484 6.69375L9.26266 6.79688H13.1392C16.9548 6.79688 17.0158 6.79688 17.1095 6.70313C17.2361 6.57656 17.2314 6.32344 17.1048 6.20625C17.0111 6.12188 16.8705 6.11719 13.1767 6.10781C11.0298 6.10313 9.30484 6.11719 9.24859 6.14063Z" fill="black"/> \
            <path d="M22.2891 8.67662C19.425 8.82193 16.9219 9.67506 15.4266 11.011C14.5828 11.761 14.1094 12.5626 13.5469 14.1844C13.3078 14.8735 12.6094 17.2735 12.6094 17.4047C12.6094 17.4422 12.6516 17.5266 12.7078 17.5969C12.825 17.7469 13.0781 17.7657 13.2047 17.6297C13.2516 17.5782 13.4109 17.0954 13.5703 16.5282L13.8516 15.5204L14.3203 15.3376C14.5781 15.2344 15.3234 15.0001 15.9797 14.8126C17.3344 14.4282 17.6297 14.3157 18.3 13.9454C19.65 13.186 20.4047 12.6001 21.7734 11.2313C22.3922 10.6172 23.1375 9.90006 23.4234 9.64693C23.7188 9.38912 23.9672 9.13131 23.9813 9.07037C24.0563 8.77506 23.8406 8.62037 23.3578 8.62975C23.1844 8.63443 22.7016 8.65787 22.2891 8.67662ZM19.8984 9.91881C18.2578 10.8047 16.4297 12.0376 15.0703 13.1719C14.8359 13.3641 14.6063 13.5516 14.5641 13.5891C14.3578 13.7532 14.9344 12.6516 15.3141 12.1547C16.1813 11.011 17.7984 10.1485 19.9453 9.68443C20.2313 9.61881 20.4844 9.56725 20.5078 9.56725C20.5359 9.56725 20.2594 9.72193 19.8984 9.91881ZM21.4031 10.6126C20.3063 11.7235 19.8188 12.136 18.8578 12.7782C17.8453 13.4485 17.2219 13.7297 15.8953 14.1094C15.2625 14.2922 14.7422 14.4282 14.7281 14.4188C14.7 14.386 15.7172 13.5329 16.4063 13.0126C18.2766 11.5969 20.2359 10.4297 21.8203 9.79225C22.1297 9.66568 22.3969 9.56256 22.4109 9.56256C22.425 9.56256 21.9703 10.036 21.4031 10.6126Z" fill="black"/> \
            <path d="M6.33735 9.79687C6.18735 9.9375 6.19672 10.1812 6.3561 10.3078C6.48266 10.4062 6.5061 10.4062 10.4155 10.4062H14.3483L14.4608 10.2891C14.5264 10.2281 14.578 10.1203 14.578 10.0547C14.578 9.98906 14.5264 9.88125 14.4608 9.82031L14.3483 9.70312H10.392C6.47797 9.70312 6.44047 9.70312 6.33735 9.79687Z" fill="black"/> \
            <path d="M6.32796 13.4062C6.2014 13.5328 6.20609 13.7859 6.33265 13.9031C6.4264 13.9875 6.54359 13.9922 9.14046 13.9922C11.7373 13.9922 11.8545 13.9875 11.9483 13.9031C12.0748 13.7859 12.0795 13.5328 11.953 13.4062C11.8592 13.3125 11.7983 13.3125 9.14046 13.3125C6.48265 13.3125 6.42171 13.3125 6.32796 13.4062Z" fill="black"/> \
            <path d="M6.46889 16.9078C6.22983 16.9969 6.15014 17.3062 6.32827 17.4844C6.41733 17.5734 6.48296 17.5781 8.40952 17.5781H10.4017L10.4955 17.4562C10.6642 17.2406 10.5986 17.0203 10.3408 16.9219C10.2095 16.875 6.60483 16.8609 6.46889 16.9078Z" fill="black"/> \
          </svg>'
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