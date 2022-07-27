"use strict";

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); Object.defineProperty(Constructor, "prototype", { writable: false }); return Constructor; }

var IDS_VALUT = {
  SEND_B_ID: "id_crop_save_button",
  CANCEL_B_ID: "id_crop_cancel_button",
  OK_B_ID: "id_crop_ok_button",
  DISMISS_B_ID: "id_crop_dismiss_button",
  GRAIN_WRAP_ID: "id_crop_entry",
  FILE_INPUT_ID: "id_crop_file",
  WORKSPACE_ID: "id_crop_modal_workspace",
  WORKSPACE_CONTAINER_ID: "id_crop-modal-container",
  MODAL_OVERLAY_ID: "id_crop-modal-overlay",
  FILE_LABEL_ID: "id_crop-file-label"
};

var ThumbnailService = /*#__PURE__*/function () {
  function ThumbnailService(i, e) {
    _classCallCheck(this, ThumbnailService);

    this.document_id = i, this.get_path = e;
  }
  function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
  }

  _createClass(ThumbnailService, [{
    key: "postThumbnail",
    value: function postThumbnail(i) {
      var e = new FormData();
      e.append("file", this._b64toBlob(i), "thumbs-"+uuidv4()+".png");
      var t = location.origin + "/api/v2/resources/" + String(this.document_id) + "/set_thumbnail";
      $.ajax({
        url: t,
        data: e,
        type: "PUT",
        contentType: !1,
        processData: !1,
        headers: {
          "X-CSRFToken": this._getCookie("csrftoken")
        },
        success: function success() {
          location.reload();
        },
        error: function error() {
          throw Error("Cannot upload new thumbnail");
        }
      });
    }
  }, {
    key: "_getCookie",
    value: function _getCookie(i) {
      var e = ("; " + document.cookie).split("; " + i + "=");
      if (2 === e.length) return e.pop().split(";").shift();
    }
  }, {
    key: "getThumbnail",
    value: function getThumbnail(i) {
      var e = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
      var t = location.origin + this.get_path + String(this.document_id);
      return $.ajax({
        url: t,
        type: "GET",
        contentType: !1,
        processData: !1,
        headers: {
          "X-CSRFToken": this._getCookie("csrftoken")
        },
        success: function success(t) {
          t && t.thumbnail_url ? i.src = t.thumbnail_url : i.src = "/static/geonode/img/missing_thumb.png", null !== e && e();
        },
        error: function error() {
          i.src = "/static/geonode/img/missing_thumb.png";
        }
      });
    }
  }, {
    key: "_b64toBlob",
    value: function _b64toBlob(i, e) {
      var t = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 512;
      e = e || "", i = i.split(",")[1];
      var s = atob(i),
          _ = [];

      for (var _i = 0; _i < s.length; _i += t) {
        var _e = s.slice(_i, _i + t),
            a = new Array(_e.length);

        for (var _i2 = 0; _i2 < _e.length; _i2++) {
          a[_i2] = _e.charCodeAt(_i2);
        }

        var r = new Uint8Array(a);

        _.push(r);
      }

      return new Blob(_, {
        type: e
      });
    }
  }]);

  return ThumbnailService;
}();

var CssManager = /*#__PURE__*/function () {
  function CssManager() {
    _classCallCheck(this, CssManager);
  }

  _createClass(CssManager, [{
    key: "makeVisible",
    value: function makeVisible(i) {
      $("#" + i).removeClass("invisible");
    }
  }, {
    key: "makeImvisible",
    value: function makeImvisible(i) {
      $("#" + i).addClass("invisible");
    }
  }, {
    key: "change_modal_visibility",
    value: function change_modal_visibility() {
      $("#" + IDS_VALUT.FILE_INPUT_ID).val() ? ($("#" + IDS_VALUT.WORKSPACE_CONTAINER_ID).removeClass("invisible"), $("#" + IDS_VALUT.MODAL_OVERLAY_ID).removeClass("invisible")) : ($("#" + IDS_VALUT.WORKSPACE_CONTAINER_ID).addClass("invisible"), $("#" + IDS_VALUT.MODAL_OVERLAY_ID).addClass("invisible"));
    }
  }]);

  return CssManager;
}();

var DomBuilder = /*#__PURE__*/function () {
  function DomBuilder(i) {
    _classCallCheck(this, DomBuilder);

    this.widget_grain = i, $(this.widget_grain).wrap(function () {
      return "<div id=".concat(IDS_VALUT.GRAIN_WRAP_ID, " class=crop-widget></div>");
    }), $(this.widget_grain).wrap(function () {
      return "";
    }), this.grain_wrapper = $("#" + IDS_VALUT.GRAIN_WRAP_ID), this.grain_wrapper.append("<div id=".concat(IDS_VALUT.MODAL_OVERLAY_ID, " class=\"crop-modal-overlay invisible\"></div>")), this.grain_wrapper.prepend('<div class="thumbnail-title">Thumbnail</div>');
  }

  _createClass(DomBuilder, [{
    key: "_create_flow_buttons",
    value: function _create_flow_buttons() {
      this.grain_wrapper.append("<input type=file id=".concat(IDS_VALUT.FILE_INPUT_ID, " name=files class=crop-input /> ")), this.grain_wrapper.append("<label id=".concat(IDS_VALUT.FILE_LABEL_ID, " for=").concat(IDS_VALUT.FILE_INPUT_ID, " class=\"btn btn-primary crop-input-label\">Change Thumbnail</label>")), this.grain_wrapper.append("<button type=button id=".concat(IDS_VALUT.SEND_B_ID, " class=\"btn btn-save invisible\">Save</button><button type=button id=").concat(IDS_VALUT.CANCEL_B_ID, " class=\"btn btn-secondary invisible\">Cancel</button>"));
    }
  }, {
    key: "create_workspace",
    value: function create_workspace() {
      var i = "\n                              <div id=".concat(IDS_VALUT.WORKSPACE_CONTAINER_ID, " class=\"crop-modal-container invisible\">                                  \n                                  <img id=").concat(IDS_VALUT.WORKSPACE_ID, " class=\"crop-modal-workspace\">                                      \n                                  <button type=button id=").concat(IDS_VALUT.OK_B_ID, " class=\"btn btn-save\">OK</button><button type=button id=").concat(IDS_VALUT.DISMISS_B_ID, " class=\"btn btn-secondary\">Dismiss</button>                                      \n                              </div>");
      $(document.body).append(i), this._create_flow_buttons();
    }
  }]);

  return DomBuilder;
}();

var CropTask = /*#__PURE__*/function () {
  function CropTask(i, e, t) {
    _classCallCheck(this, CropTask);

    this.dom_builder = i, this.css_manager = e, this.previous_image = null, this.data_service = t;
  }

  _createClass(CropTask, [{
    key: "init_cropper",
    value: function init_cropper() {
      this.cropper = new Cropper($("#" + IDS_VALUT.WORKSPACE_ID)[0], {
        aspectRatio: 4 / 3,
        crop: function crop(i) {}
      });
    }
  }, {
    key: "set_previous_image",
    value: function set_previous_image(i) {
      this.previous_image = i;
    }
  }, {
    key: "init",
    value: function init() {
      this.dom_builder.create_workspace(), $("#" + IDS_VALUT.FILE_INPUT_ID).on("change", this.load_start_image.bind(this)), $("#" + IDS_VALUT.DISMISS_B_ID).on("click", this.dismiss_current_image.bind(this)), $("#" + IDS_VALUT.OK_B_ID).on("click", this.apply_current_image.bind(this)), $("#" + IDS_VALUT.CANCEL_B_ID).on("click", this.cancel_cropping.bind(this)), $("#" + IDS_VALUT.SEND_B_ID).on("click", this.send_cropped_image.bind(this)), this.previous_image = this.dom_builder.widget_grain.src;
    }
  }, {
    key: "load_start_image",
    value: function load_start_image(i) {
      var _this = this;

      if (!(window.File && window.FileReader && window.FileList && window.Blob)) throw Error("FileAPI is not supported");

      if (i.target.files.length) {
        var e = i.target.files[0],
            t = new FileReader();
        t.onload = function (i) {
          _this.cropper && _this.cropper.destroy(), $("#" + IDS_VALUT.WORKSPACE_ID).attr("src", i.target.result);
        }, t.onloadend = function (i) {
          _this.init_cropper(), _this.css_manager.change_modal_visibility();
        }, t.readAsDataURL(e);
      }
    }
  }, {
    key: "_clear_input",
    value: function _clear_input() {
      $("#" + IDS_VALUT.FILE_INPUT_ID).val("");
    }
  }, {
    key: "dismiss_current_image",
    value: function dismiss_current_image() {
      this._clear_input(), this.cropper.destroy(), this.css_manager.change_modal_visibility();
    }
  }, {
    key: "apply_current_image",
    value: function apply_current_image() {
      var i = this.dom_builder.widget_grain.height,
          e = this.dom_builder.widget_grain.width;
      $(this.dom_builder.widget_grain).attr("src", this.cropper.getCroppedCanvas({
        width: 400
      }).toDataURL()), $(this.dom_builder.widget_grain).attr("height", i), $(this.dom_builder.widget_grain).attr("width", e), this.css_manager.makeImvisible(IDS_VALUT.FILE_LABEL_ID), this.css_manager.makeImvisible(IDS_VALUT.FILE_INPUT_ID), this.css_manager.makeVisible(IDS_VALUT.SEND_B_ID), this.css_manager.makeVisible(IDS_VALUT.CANCEL_B_ID), this.cropper.destroy(), this._clear_input(), this.css_manager.change_modal_visibility();
    }
  }, {
    key: "cancel_cropping",
    value: function cancel_cropping() {
      $(this.dom_builder.widget_grain).attr("src", this.previous_image), this._clear_input(), this.css_manager.makeImvisible(IDS_VALUT.CANCEL_B_ID), this.css_manager.makeImvisible(IDS_VALUT.SEND_B_ID), this.css_manager.makeVisible(IDS_VALUT.FILE_INPUT_ID), this.css_manager.makeVisible(IDS_VALUT.FILE_LABEL_ID);
    }
  }, {
    key: "send_cropped_image",
    value: function send_cropped_image() {
      this.set_previous_image(this.dom_builder.widget_grain.src), this.data_service.postThumbnail(this.previous_image), this.css_manager.makeVisible(IDS_VALUT.FILE_INPUT_ID), this.css_manager.makeImvisible(IDS_VALUT.SEND_B_ID), this.css_manager.makeImvisible(IDS_VALUT.CANCEL_B_ID);
    }
  }]);

  return CropTask;
}();

var CropWidget = /*#__PURE__*/function () {
  function CropWidget(i, e, t) {
    var s = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : null;

    _classCallCheck(this, CropWidget);

    if (this.element = i, "IMG" !== this.element.tagName) throw Error("Base element should be <img>");
    this.dom_builder = new DomBuilder(this.element), this.css_manager = new CssManager(), this.service = new ThumbnailService(e, t), this.crop = null, this.prefetch_image = s;
  }

  _createClass(CropWidget, [{
    key: "init",
    value: function init() {
      this.crop = new CropTask(this.dom_builder, this.css_manager, this.service), "" === this.prefetch_image ? (this.element.src = "/static/geonode/img/missing_thumb.png", this.crop.init()) : null === this.prefetch_image || void 0 === this.prefetch_image ? this.service.getThumbnail(this.element, this.crop.init.bind(this.crop)) : (this.element.src = this.prefetch_image, this.crop.init());
    }
  }]);

  return CropWidget;
}();
//# sourceMappingURL=crop_widget_es5.js.map
