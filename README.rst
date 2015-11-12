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


Plans
-----

*November 12, 2015*–A long time ago we started a `2.0 Milestone`_ then when
got really busy with other areas of Pinax, our day jobs, and life. Today, we
getting back into the swing of things starting with this ``long-overdue-updates``
branch that initially is just doing a bit of clean up.

These items will be made into issues in the `2.0 Milestone`_. Links will be
added to them once they do:

* address namespace issue with ``payments`` - `Issue #169`_
* full Python 3 compatibility (DSP should support every Python that Django supports) - `Issue #170`_
* make sure custom user model support is fully in place - `Issue #172`_
* support Django 1.7, 1.8, 1.9 (currently ``master``) - `Issue #171`_
* add migrations - `Issue #164`_
* support for the following Stripe services:
  * File Uploads - `Issue #175`_ (later milestone)
  * Connect - `Issue #174`_ (later milestone)
  * Bitcoin - `Issue #176`_ (later milestone)
  * Alipay - `Issue #177`_ (later milestone)
  * ACH - `Issue #173`_
* update for latest / greatest API compatiblity - `Issue #178`_
* refactor out ``payments/settings.py`` to ``payments/conf.py`` to support django-appconf or do something with ``payments/apps.py`` - `Issue #179`_
* add hooksets for key points of extensibility - `Issue #180`_
* convert ajax views to CBVs - `Issue #181`_
* add new webhooks - `Issue #182`_
* better handling of one-off charges - `Issue #43`_


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


.. _2.0 Milestone: https://github.com/pinax/django-stripe-payments/issues?q=is%3Aopen+is%3Aissue+milestone%3A2.0
.. _Issue #169: https://github.com/pinax/django-stripe-payments/issues/169
.. _Issue #170: https://github.com/pinax/django-stripe-payments/issues/170
.. _Issue #171: https://github.com/pinax/django-stripe-payments/issues/171
.. _Issue #172: https://github.com/pinax/django-stripe-payments/issues/172
.. _Issue #164: https://github.com/pinax/django-stripe-payments/issues/164
.. _Issue #173: https://github.com/pinax/django-stripe-payments/issues/173
.. _Issue #174: https://github.com/pinax/django-stripe-payments/issues/174
.. _Issue #175: https://github.com/pinax/django-stripe-payments/issues/175
.. _Issue #176: https://github.com/pinax/django-stripe-payments/issues/176
.. _Issue #177: https://github.com/pinax/django-stripe-payments/issues/177
.. _Issue #178: https://github.com/pinax/django-stripe-payments/issues/178
.. _Issue #179: https://github.com/pinax/django-stripe-payments/issues/179
.. _Issue #180: https://github.com/pinax/django-stripe-payments/issues/180
.. _Issue #181: https://github.com/pinax/django-stripe-payments/issues/181
.. _Issue #182: https://github.com/pinax/django-stripe-payments/issues/182
.. _Issue #43: https://github.com/pinax/django-stripe-payments/issues/43
