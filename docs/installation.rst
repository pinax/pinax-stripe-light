.. _installation:

Requirements
============

The models and management commands should work without any additional requirements, but if you want to use the templates, specially the templates involving forms,
that ship with this app, then you will need ``django-forms-bootstrap`` and ``eldarion-ajax``.

Add ``django-forms-bootstrap`` to your project::

    pip install django-forms-bootstrap

You will also want to add ``django_forms_bootstrap`` to your `INSTALLED_APPS``::

    INSTALLED_APPS = [
        "django_forms_bootstrap",
    ]

You will need to add the request context processor to TEMPLATE_CONTEXT_PROCESSORS
if you wish to use the included templates by adding something like this in our
settings.py::

    TEMPLATE_CONTEXT_PROCESSORS += (
        'django.core.context_processors.request',
    )

Add ``eldarion-ajax.js`` to your base template. eldarion-ajax_
is a library used by the included templates to interact with the ajax views. You
can certainly write your own javascript, but it is likely easier for you to just
include the library.

Get it here: eldarion-ajax_


Installation
============

* To install ::

    pip install django-stripe-payments


* Add ``'payments'`` to your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = [
        "payments",
    ]
    
* Add ``'payments'`` to your ``urls.py`` ::

    urlpatterns = patterns("",
        ...
        url(r"^payments/", include("payments.urls")),
        ...
    )

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

An example of integrating Checkout_ is to put this in your base template::

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


.. _eldarion-ajax: https://github.com/eldarion/bootstrap-ajax
.. _Checkout: https://stripe.com/docs/checkout

