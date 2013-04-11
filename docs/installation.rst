.. _installation:

Requirements
============

If you want to use the templates, specially the templates involving forms,
that ship with this app, then you will need to add ``django-forms-bootstrap``
to your project::

    pip install django-forms-bootstrap

You will also want to add ``django_forms_bootstrap`` to your `INSTALLED_APPS``::

    INSTALLED_APPS = [
        "django_forms_bootstrap",
    ]


Installation
============

* To install ::

    pip install django-stripe-payments


* Add ``'payments'`` to your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = [
        "payments",
    ]

Configuration (Modifications to `settings.py`)
=======================
* Add entries to for your publishable and secret keys. The recommended method is 
  to setup your production keys using environment variables.  This helps to keep them 
  more secure.  Your test keys can be displayed in your code directly.

  The following entries look for your STRIPE_PUBLIC_KEY and
  STRIPE_SECRET_KEY in your environment and, if it can't find them, 
  uses your test keys values instead::

    STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "<your publishable test key>")
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "<your secret test key>")

* Setup your payment plans by defining the setting ``PAYMENTS_PLANS``::

    PAYMENTS_PLANS = {
        "monthly": {
            "stripe_plan_id": "pro-monthly",
            "name": "Web App Pro ($25/month)",
            "description": "The monthly subscription plan to WebApp",
            "price": 25,
            "currency": "usd",
            "interval": "month"
        },
        "yearly": {
            "stripe_plan_id": "pro-yearly",
            "name": "Web App Pro ($199/year)",
            "description": "The annual subscription plan to WebApp",
            "price": 199,
            "currency": "usd",
            "interval": "year"
        }
    }


Static Media
============

The included templates have been tested to work with Checkout_.

An example of integrating Checkout_ is to pus this in your base template::

    <script src="//checkout.stripe.com/v2/checkout.js"></script>
    <script>
        $(function() {
            $('body').on("click", '.change-card, .subscribe-form button[type=submit]', function(e) {
              e.preventDefault();
              var $form = $(this).closest("form"),
                  token = function(res) {
                    $form.find("input[name=stripe_token]").val(res.id);
                    $form.trigger("submit");
                  };
     
              StripeCheckout.open({
                key:         $form.data("stripe-key"),
                name:        'Payment Method',
                panelLabel:  'Add Payment Method',
                token:       token
              });
     
              return false;
            });
        });
    </script>


.. _Checkout: https://stripe.com/docs/checkout
