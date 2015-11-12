======================
Django Stripe Payments
======================

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


Pinax
------

Pinax is an open-source platform built on the Django Web Framework. It is an ecosystem of reusable Django apps, themes, and starter project templates.
This collection can be found at http://pinaxproject.com.

This app was developed as part of the Pinax ecosystem but is just a Django app and can be used independently of other Pinax apps.


django-stripe-payments
-----------------------

``django-stripe-payments`` is a payments Django app for Stripe.

This app allows you to process one off charges as well as signup users for
recurring subscriptions managed by Stripe.

Some suggested integration steps:
  1. Overload the templates provided to use your inheritance tree (for bases etc) and block names.
  2. Point your stripe account at the webhook address in the payments urls.
  3. Add the static media snippet from here (or else nothing will actually talk to stripe):
    * http://django-stripe-payments.readthedocs.org/en/latest/installation.html#configuration-modifications-to-settings-py
  4. Set up SSL if you have not already.
  5. Define some plans (see docs).
  6. Run syncdb to generate the necessary tables, then init_plans and init_customers.


Development
------------

To run test suite::

    $ pip install detox
    $ detox


Documentation
--------------
Documentation for django-stripe-payments can be found at http://django-stripe-payments.readthedocs.org
The Pinax documentation is available at http://pinaxproject.com/pinax/.


Code of Conduct
-----------------

In order to foster a kind, inclusive, and harassment-free community, the Pinax Project has a code of conduct, which can be found here  http://pinaxproject.com/pinax/code_of_conduct/.


Pinax Project Blog and Twitter
-------------------------------
For updates and news regarding the Pinax Project, please follow us on Twitter at @pinaxproject and check out our blog http://blog.pinaxproject.com.
