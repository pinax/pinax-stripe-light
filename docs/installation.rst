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

* Setup your publishable and secret keys. The recommended method is to have
  and environment variable override defaults and set the defaults as your test
  keys and then in production set your production keys in your environment::

    STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "<the publishable test key>")
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "<the secret test key>")

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

* Add the context processor to your ``settings.py``::

    TEMPLATE_CONTEXT_PROCESSORS = [
        ...
        "payments.context_processors.payments_settings",
        ...
    ]


Static Media
============

The included templates have been tested to work with Checkout_.

.. _Checkout: https://stripe.com/docs/checkout

    