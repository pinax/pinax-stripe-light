.. _installation:

Installation
============

* To install ::

    pip install django-stripe-payments


* Add ``'payments'`` to your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # other apps
        "payments",
    )

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
            "interval": "month"
        },
        "yearly": {
            "stripe_plan_id": "pro-yearly",
            "name": "Web App Pro ($199/year)",
            "description": "The annual subscription plan to WebApp",
            "price": 199,
            "interval": "year"
        }
    }

* Add the context processor to your ``settings.py``::

    TEMPLATE_CONTEXT_PROCESSORS = [
        ...
        "payments.context_processors.payments_settings",
        ...
    ]
