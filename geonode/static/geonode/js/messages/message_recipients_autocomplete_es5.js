"use strict";

function _toConsumableArray(t) { return _arrayWithoutHoles(t) || _iterableToArray(t) || _unsupportedIterableToArray(t) || _nonIterableSpread() }

function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.") }

function _unsupportedIterableToArray(t, e) { if (t) { if ("string" == typeof t) return _arrayLikeToArray(t, e); var r = Object.prototype.toString.call(t).slice(8, -1); return "Object" === r && t.constructor && (r = t.constructor.name), "Map" === r || "Set" === r ? Array.from(t) : "Arguments" === r || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(r) ? _arrayLikeToArray(t, e) : void 0 } }

function _iterableToArray(t) { if ("undefined" != typeof Symbol && Symbol.iterator in Object(t)) return Array.from(t) }

function _arrayWithoutHoles(t) { if (Array.isArray(t)) return _arrayLikeToArray(t) }

function _arrayLikeToArray(t, e) {
    (null == e || e > t.length) && (e = t.length); for (var r = 0, n = new Array(e); r < e; r++) n[r] = t[r]; return n }

function _classCallCheck(t, e) { if (!(t instanceof e)) throw new TypeError("Cannot call a class as a function") }

function _defineProperties(t, e) { for (var r = 0; r < e.length; r++) { var n = e[r];
        n.enumerable = n.enumerable || !1, n.configurable = !0, "value" in n && (n.writable = !0), Object.defineProperty(t, n.key, n) } }

function _createClass(t, e, r) { return e && _defineProperties(t.prototype, e), r && _defineProperties(t, r), t }

function get_users_data(t) { return t.objects.map(function(t) { return { value: t.username, id: t.id } }) }

function get_groups_data(t) { return t.objects.map(function(t) { return { value: t.title, id: t.id } }) }
var MessageRecipientsTags = function() {
    function t(e, r, n) { var i = arguments.length > 3 && void 0 !== arguments[3] ? arguments[3] : []; if (_classCallCheck(this, t), "INPUT" !== e.tagName || "text" !== e.type) throw Error('Base element should be <input type="text">');
        this.input = e, this.tagify = null, this.data_extract_func = r, this.url = n, this.blacklist = i, this.request_controller = null } return _createClass(t, [{ key: "init", value: function() { this.tagify = new Tagify(this.input, { whitelist: [], blacklist: this.blacklist }), this.tagify.on("input", this._onInputHandler.bind(this)), this.request_controller = new AbortController } }, { key: "_onInputHandler", value: function(t) { var e = this,
                r = t.detail.value;
            this.tagify.settings.whitelist.length = 0, this.tagify.loading(!0).dropdown.hide.call(this.tagify), this.request_controller.abort(), this.request_controller = new AbortController, fetch(this.url + r, { signal: this.request_controller.signal }).then(function(t) { return t.json().then(e.data_extract_func).then(function(t) { var n;
                    t = t.filter(function(t) { if (!e.blacklist.includes(t.value)) return t }), (n = e.tagify.settings.whitelist).splice.apply(n, [0, t.length].concat(_toConsumableArray(t))), e.tagify.loading(!1).dropdown.show.call(e.tagify, r) }) }) } }, { key: "fixOutputValue", value: function() { var t = this; "" !== this.input.value && JSON.parse(this.input.value).filter(function(t) { return "id" in t }).forEach(function(e) { $("<input>").attr({ type: "hidden", id: "foo", name: t.input.name, value: e.id }).appendTo("form") }), this.input.disabled = !0 } }]), t }();