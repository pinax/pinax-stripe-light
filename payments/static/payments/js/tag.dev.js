(function() {
  var $, global, script,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __slice = [].slice;

  $ = this.jQuery || this.Zepto;

  if (!$) {
    throw 'jQuery/Zepto required';
  }

  this.PaymentTag = (function() {

    PaymentTag.replaceTags = function(element) {
      var _this = this;
      if (element == null) {
        element = document.body;
      }
      return $('payment, .payment-tag', element).each(function(i, tag) {
        return new _this({
          el: tag
        }).render();
      });
    };

    PaymentTag.prototype.defaults = {
      tokenName: 'stripe_token',
      token: true,
      cvc: true
    };

    function PaymentTag(options) {
      var _ref, _ref1;
      if (options == null) {
        options = {};
      }
      this.changeCardType = __bind(this.changeCardType, this);

      this.restrictNumeric = __bind(this.restrictNumeric, this);

      this.formatNumber = __bind(this.formatNumber, this);

      this.handleToken = __bind(this.handleToken, this);

      this.submit = __bind(this.submit, this);

      this.$el = options.el || '<payment />';
      this.$el = $(this.$el);
      options.key || (options.key = this.$el.attr('key') || this.$el.attr('data-key'));
      if ((_ref = options.cvc) == null) {
        options.cvc = !((this.$el.attr('nocvc') != null) || (this.$el.attr('data-nocvc') != null));
      }
      if ((_ref1 = options.token) == null) {
        options.token = !((this.$el.attr('notoken') != null) || (this.$el.attr('data-notoken') != null));
      }
      options.form || (options.form = this.$el.parents('form'));
      this.options = $.extend({}, this.defaults, options);
      if (this.options.key) {
        this.setKey(this.options.key);
      }
      this.setForm(this.options.form);
      this.$el.delegate('.number input', 'keydown', this.formatNumber);
      this.$el.delegate('.number input', 'keyup', this.changeCardType);
      this.$el.delegate('input[type=tel]', 'keypress', this.restrictNumeric);
    }

    PaymentTag.prototype.render = function() {
      this.$el.html(this.constructor.view(this));
      this.$number = this.$('.number input');
      this.$cvc = this.$('.cvc input');
      this.$expiryMonth = this.$('.expiry input.expiryMonth');
      this.$expiryYear = this.$('.expiry input.expiryYear');
      this.$message = this.$('.message');
      return this;
    };

    PaymentTag.prototype.renderToken = function(token) {
      this.$token = $('<input type="hidden">');
      this.$token.attr('name', this.options.tokenName);
      this.$token.val(token);
      return this.$el.html(this.$token);
    };

    PaymentTag.prototype.setForm = function($form) {
      this.$form = $($form);
      return this.$form.bind('submit.payment', this.submit);
    };

    PaymentTag.prototype.setKey = function(key) {
      this.key = key;
      return Stripe.setPublishableKey(this.key);
    };

    PaymentTag.prototype.validate = function() {
      var expiry, valid;
      valid = true;
      this.$('div').removeClass('invalid');
      this.$message.empty();
      if (!Stripe.validateCardNumber(this.$number.val())) {
        valid = false;
        this.handleError({
          code: 'invalid_number'
        });
      }
      expiry = this.expiryVal();
      if (!Stripe.validateExpiry(expiry.month, expiry.year)) {
        valid = false;
        this.handleError({
          code: 'expired_card'
        });
      }
      if (this.options.cvc && !Stripe.validateCVC(this.$cvc.val())) {
        valid = false;
        this.handleError({
          code: 'invalid_cvc'
        });
      }
      if (!valid) {
        this.$('.invalid input:first').select();
      }
      return valid;
    };

    PaymentTag.prototype.createToken = function(callback) {
      var complete, expiry,
        _this = this;
      complete = function(status, response) {
        if (response.error) {
          return callback(response.error);
        } else {
          return callback(null, response);
        }
      };
      expiry = this.expiryVal();
      return Stripe.createToken({
        number: this.$number.val(),
        cvc: this.$cvc.val() || null,
        exp_month: expiry.month,
        exp_year: expiry.year
      }, complete);
    };

    PaymentTag.prototype.submit = function(e) {
      if (e != null) {
        e.preventDefault();
      }
      if (e != null) {
        e.stopImmediatePropagation();
      }
      if (!this.validate()) {
        return;
      }
      if (this.pending) {
        return;
      }
      this.pending = true;
      this.disableInputs();
      this.trigger('pending');
      this.$el.addClass('pending');
      return this.createToken(this.handleToken);
    };

    PaymentTag.prototype.handleToken = function(err, response) {
      this.enableInputs();
      this.trigger('complete');
      this.$el.removeClass('pending');
      this.pending = false;
      if (err) {
        return this.handleError(err);
      } else {
        this.trigger('success', response);
        this.$el.addClass('success');
        if (this.options.token) {
          this.renderToken(response.id);
        }
        this.$form.unbind('submit.payment', this.submit);
        return this.$form.submit();
      }
    };

    PaymentTag.prototype.formatNumber = function(e) {
      var digit, lastDigits, value;
      digit = String.fromCharCode(e.which);
      if (!/^\d+$/.test(digit)) {
        return;
      }
      value = this.$number.val();
      if (Stripe.cardType(value) === 'American Express') {
        lastDigits = value.match(/^(\d{4}|\d{4}\s\d{6})$/);
      } else {
        lastDigits = value.match(/(?:^|\s)(\d{4})$/);
      }
      if (lastDigits) {
        return this.$number.val(value + ' ');
      }
    };

    PaymentTag.prototype.restrictNumeric = function(e) {
      var char;
      if (e.shiftKey || e.metaKey) {
        return true;
      }
      if (e.which === 0) {
        return true;
      }
      char = String.fromCharCode(e.which);
      return !/[A-Za-z]/.test(char);
    };

    PaymentTag.prototype.cardTypes = {
      'Visa': 'visa',
      'American Express': 'amex',
      'MasterCard': 'mastercard',
      'Discover': 'discover',
      'Unknown': 'unknown'
    };

    PaymentTag.prototype.changeCardType = function(e) {
      var map, name, type, _ref;
      type = Stripe.cardType(this.$number.val());
      if (!this.$number.hasClass(type)) {
        _ref = this.cardTypes;
        for (name in _ref) {
          map = _ref[name];
          this.$number.removeClass(map);
        }
        return this.$number.addClass(this.cardTypes[type]);
      }
    };

    PaymentTag.prototype.handleError = function(err) {
      if (err.message) {
        this.$message.text(err.message);
      }
      switch (err.code) {
        case 'card_declined':
          this.invalidInput(this.$number);
          break;
        case 'invalid_number':
        case 'incorrect_number':
          this.invalidInput(this.$number);
          break;
        case 'invalid_expiry_month':
          this.invalidInput(this.$expiryMonth);
          break;
        case 'invalid_expiry_year':
        case 'expired_card':
          this.invalidInput(this.$expiryYear);
          break;
        case 'invalid_cvc':
          this.invalidInput(this.$cvc);
      }
      this.$('label.invalid:first input').select();
      this.trigger('error', err);
      return typeof console !== "undefined" && console !== null ? console.error('Stripe error:', err) : void 0;
    };

    PaymentTag.prototype.invalidInput = function(input) {
      input.parent().addClass('invalid');
      return this.trigger('invalid', [input.attr('name'), input]);
    };

    PaymentTag.prototype.expiryVal = function() {
      var month, prefix, trim, year;
      trim = function(s) {
        return s.replace(/^\s+|\s+$/g, '');
      };
      month = trim(this.$expiryMonth.val());
      year = trim(this.$expiryYear.val());
      if (year.length === 2) {
        prefix = (new Date).getFullYear();
        prefix = prefix.toString().slice(0, 2);
        year = prefix + year;
      }
      return {
        month: month,
        year: year
      };
    };

    PaymentTag.prototype.enableInputs = function() {
      var $elements;
      $elements = this.$el.add(this.$form).find(':input');
      return $elements.each(function() {
        var $item, _ref;
        $item = $(this);
        return $elements.attr('disabled', (_ref = $item.data('olddisabled')) != null ? _ref : false);
      });
    };

    PaymentTag.prototype.disableInputs = function() {
      var $elements;
      $elements = this.$el.add(this.$form).find(':input');
      return $elements.each(function() {
        var $item;
        $item = $(this);
        $item.data('olddisabled', $item.attr('disabled'));
        return $item.attr('disabled', true);
      });
    };

    PaymentTag.prototype.trigger = function() {
      var data, event, _ref;
      event = arguments[0], data = 2 <= arguments.length ? __slice.call(arguments, 1) : [];
      return (_ref = this.$el).trigger.apply(_ref, ["" + event + ".payment"].concat(__slice.call(data)));
    };

    PaymentTag.prototype.$ = function(sel) {
      return $(sel, this.$el);
    };

    return PaymentTag;

  })();

  document.createElement('payment');

  if (typeof module !== "undefined" && module !== null) {
    module.exports = PaymentTag;
  }

  global = this;

  if (global.Stripe) {
    $(function() {
      return typeof PaymentTag.replaceTags === "function" ? PaymentTag.replaceTags() : void 0;
    });
  } else {
    script = document.createElement('script');
    script.onload = script.onreadystatechange = function() {
      if (!global.Stripe) {
        return;
      }
      if (script.done) {
        return;
      }
      script.done = true;
      return typeof PaymentTag.replaceTags === "function" ? PaymentTag.replaceTags() : void 0;
    };
    script.src = 'https://js.stripe.com/v1/';
    $(function() {
      var sibling;
      sibling = document.getElementsByTagName('script')[0];
      return sibling != null ? sibling.parentNode.insertBefore(script, sibling) : void 0;
    });
  }

}).call(this);
(function() {
  this.PaymentTag || (this.PaymentTag = {});
  this.PaymentTag["view"] = function(__obj) {
    if (!__obj) __obj = {};
    var __out = [], __capture = function(callback) {
      var out = __out, result;
      __out = [];
      callback.call(this);
      result = __out.join('');
      __out = out;
      return __safe(result);
    }, __sanitize = function(value) {
      if (value && value.ecoSafe) {
        return value;
      } else if (typeof value !== 'undefined' && value != null) {
        return __escape(value);
      } else {
        return '';
      }
    }, __safe, __objSafe = __obj.safe, __escape = __obj.escape;
    __safe = __obj.safe = function(value) {
      if (value && value.ecoSafe) {
        return value;
      } else {
        if (!(typeof value !== 'undefined' && value != null)) value = '';
        var result = new String(value);
        result.ecoSafe = true;
        return result;
      }
    };
    if (!__escape) {
      __escape = __obj.escape = function(value) {
        return ('' + value)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;');
      };
    }
    (function() {
      (function() {
      
        __out.push('<span class="message"></span>\n\n<div class="number">\n  <label for="paymentNumber">Card number</label>\n\n  <input type="tel" id="paymentNumber" placeholder="4242 4242 4242 4242" autofocus required>\n</div>\n\n<div class="expiry">\n  <label for="paymentExpiryMonth">Expiry date <em>(mm/yy)</em></label>\n\n  <input class="expiryMonth" type="tel" id="paymentExpiryMonth" placeholder="mm" required>\n  <input class="expiryYear" type="tel" id="paymentExpiryYear" placeholder="yy" required>\n</div>\n\n');
      
        if (this.options.cvc) {
          __out.push('\n  <div class="cvc">\n    <label for="paymentCVC">Security code</label>\n    <input type="tel" id="paymentCVC" placeholder="123" maxlength="4" required>\n  </div>\n');
        }
      
        __out.push('\n');
      
      }).call(this);
      
    }).call(__obj);
    __obj.safe = __objSafe, __obj.escape = __escape;
    return __out.join('');
  };
}).call(this);
