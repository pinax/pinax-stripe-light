======================
django-stripe-payments
======================

a payments Django app for Stripe

.. image:: http://slack.pinaxproject.com/badge.svg
    :target: http://slack.pinaxproject.com/

.. image:: https://img.shields.io/travis/pinax/django-stripe-payments.svg
    :target: https://travis-ci.org/pinax/django-stripe-payments

.. image:: https://img.shields.io/coveralls/pinax/django-stripe-payments.svg
    :target: https://coveralls.io/r/pinax/django-stripe-payments

.. image:: https://img.shields.io/pypi/dm/django-stripe-payments.svg
    :target:  https://pypi.python.org/pypi/django-stripe-payments/

.. image:: https://img.shields.io/pypi/v/django-stripe-payments.svg
    :target:  https://pypi.python.org/pypi/django-stripe-payments/

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target:  https://pypi.python.org/pypi/django-stripe-payments/


This app allows you to process one off charges as well as signup users for
recurring subscriptions managed by Stripe.

Documentation can be found at http://django-stripe-payments.readthedocs.org

Some suggested integration steps:
  1. Overload the templates provided to use your inheritance tree (for bases etc) and block names.
  2. Point your stripe account at the webhook address in the payments urls.
  3. Add the static media snippet from here (or else nothing will actually talk to stripe):
    * http://django-stripe-payments.readthedocs.org/en/latest/installation.html#configuration-modifications-to-settings-py
  4. Set up SSL if you have not already.
  5. Define some plans (see docs).
  6. Run syncdb to generate the necessary tables, then init_plans and init_customers.

Development
-----------

To run test suite::

    $ pip install detox
    $ detox
