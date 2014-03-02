======================
django-stripe-payments
======================

a payments Django app for Stripe

.. image:: https://travis-ci.org/eldarion/django-stripe-payments.png
    :target: https://travis-ci.org/eldarion/django-stripe-payments

.. image:: https://coveralls.io/repos/eldarion/django-stripe-payments/badge.png
    :target: https://coveralls.io/r/eldarion/django-stripe-payments

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

    $ pip install Django stripe django-nose django-jsonfield mock
    $ python runtests.py


Commercial Support
------------------

This app, and many others like it, have been built in support of many of Eldarion's
own sites, and sites of our clients. We would love to help you on your next project
so get in touch by dropping us a note at info@eldarion.com.
