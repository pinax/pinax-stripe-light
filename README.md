# Pinax Stripe

[![](http://slack.pinaxproject.com/badge.svg)](http://slack.pinaxproject.com/)
[![](https://img.shields.io/travis/pinax/pinax-stripe.svg)](https://travis-ci.org/pinax/pinax-stripe)
[![](https://img.shields.io/coveralls/pinax/pinax-stripe.svg)](https://coveralls.io/r/pinax/pinax-stripe)
[![](https://img.shields.io/pypi/dm/pinax-stripe.svg)](https://pypi.python.org/pypi/pinax-stripe/)
[![](https://img.shields.io/pypi/v/pinax-stripe.svg)](https://pypi.python.org/pypi/pinax-stripe/)
[![](https://img.shields.io/badge/license-MIT-blue.svg)](https://pypi.python.org/pypi/pinax-stripe/)


This app was formerly called `django-stripe-payments` and has been renamed to
avoid namespace collisions and to have more consistency with Pinax.

---

## Refactor and Update Plans

***November 22, 2015***

Phew! 10 days and almost 100 commits later and milestone is as far as I know
code complete.  The only remaining tasks are:

* [ ] writing documentation - lots has changes, drastically, time to throw out the current docs and write a comprehensive set from scratch
* [ ] review current test coverage and improve on it if the gaps that are open look critical
* [ ] package up the templates I've been testing with in a new release of [pianx-theme-bootstrap](http://github.com/pinax/pinax-theme-bootstrap)
* [ ] put together a demo starter project (this one i might hold off until after 2.0 ships)


***November 12, 2015***

A long time ago we started a [2.0 Milestone](https://github.com/pinax/django-stripe-payments/issues?q=is%3Aopen+is%3Aissue+milestone%3A2.0) then when
got really busy with other areas of Pinax, our day jobs, and life. Today, we
getting back into the swing of things starting with merging of the  `long-overdue-updates`
branch.

These items will be made into issues in the [2.0 Milestone](https://github.com/pinax/django-stripe-payments/issues?q=is%3Aopen+is%3Aissue+milestone%3A2.0).

* [x] address namespace issue with `payments` - [Issue #169](https://github.com/pinax/django-stripe-payments/issues/169)
* [x] full Python 3 compatibility (DSP should support every Python that Django supports) - [Issue #170](https://github.com/pinax/django-stripe-payments/issues/170)
* [x] make sure custom user model support is fully in place - [Issue #172](https://github.com/pinax/django-stripe-payments/issues/172)
* [x] support Django 1.7, 1.8, 1.9 (currently ``master``) - [Issue #171](https://github.com/pinax/django-stripe-payments/issues/171)
* [x] refactor out ``payments/settings.py`` to ``payments/conf.py`` to support django-appconf or do something with ``payments/apps.py`` - [Issue #179](https://github.com/pinax/django-stripe-payments/issues/179)
* [x] add hooksets for key points of extensibility - [Issue #180](https://github.com/pinax/django-stripe-payments/issues/180)
* [x] convert ajax views to CBVs - [Issue #181](https://github.com/pinax/django-stripe-payments/issues/181)
* [x] add migrations - [Issue #164](https://github.com/pinax/django-stripe-payments/issues/164)
* [x] update for latest / greatest API compatibility - [Issue #178](https://github.com/pinax/django-stripe-payments/issues/178)
* [x] add new webhooks - [Issue #182](https://github.com/pinax/django-stripe-payments/issues/182)

Subsequent (shorter) milestones involve adding support for the following Stripe services:

* [ ] ACH - [Issue #173](https://github.com/pinax/django-stripe-payments/issues/173)
* [ ] Connect - [Issue #174](https://github.com/pinax/django-stripe-payments/issues/174)
* [ ] File Uploads - [Issue #175](https://github.com/pinax/django-stripe-payments/issues/175)
* [ ] Bitcoin - [Issue #176](https://github.com/pinax/django-stripe-payments/issues/176)
* [ ] Alipay - [Issue #177](https://github.com/pinax/django-stripe-payments/issues/177)

---

## Pinax

Pinax is an open-source platform built on the Django Web Framework. It is an ecosystem of reusable Django apps, themes, and starter project templates.
This collection can be found at http://pinaxproject.com.

This app was developed as part of the Pinax ecosystem but is just a Django app and can be used independently of other Pinax apps.


## pinax-stripe

`pinax-stripe` is a payments Django app for Stripe.

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


## Development

`pinax-stripe` supports a variety of Python and Django versions. It's best if you test each one of these before committing. Our [Travis CI Integration](https://travis-ci.org/pinax/pinax-stripe) will test these when you push but knowing before you commit prevents from having to do a lot of extra commits to get the build to pass.

### Environment Setup

In order to easily test on all these Pythons and run the exact same thing that Travis CI will execute you'll want to setup [pyenv](https://github.com/yyuu/pyenv) and install the Python versions outlined in [tox.ini](tox.ini).

If you are on the Mac, it's recommended you use [brew](http://brew.sh/). After installing `brew` run:

```
$ brew install pyenv pyenv-virtualenv pyenv-virtualenvwrapper
```

Then:

```
$ CFLAGS="-I$(xcrun --show-sdk-path)/usr/include -I$(brew --prefix openssl)/include" \
LDFLAGS="-L$(brew --prefix openssl)/lib" \
pyenv install 2.7.10 3.2.6 3.3.6 3.4.3 3.5.0

$ pyenv virtualenv 2.7.10 test-2.7.10
$ pyenv virtualenv 3.2.6 test-3.2.6
$ pyenv virtualenv 3.3.6 test-3.3.6
$ pyenv virtualenv 3.4.3 test-3.4.3
$ pyenv virtualenv 3.5.0 test-3.5.0
$ pyenv global 2.7.10 test-2.7.10 test-3.2.6 test-3.2.6 test-3.3.6 test-3.4.3 test-3.5.0

$ pip install detox
```

To run test suite:

Make sure you are not inside a `virtualenv` and then:

```
$ detox
```

This will execute the testing matrix in parallel as defined in the `tox.ini`.


## API

In order to make this app more maintainable and scale with all the services that
Stripe is offering, we have refactored this internal API away from being just
model methods into a service layer in `pinax.stripe.actions`.

Internally, things like views, management commands, and receivers, all flow
through the public API defined in the `pinax.stripe.actions` modules.  These
modules interact with both the Stripe API as well as `pinax-stripe`'s internal
models. To interface with the models, they work through a set of proxy models
found in `pinax.stripe.proxies`.  Methods on this proxy models are for internal
use only and provide a clean separation from the actual models.

### Charges


### Customers


### Events


### Invoices


### Refunds


### Sources


### Subscriptions


### Syncs



## Documentation

Documentation for django-stripe-payments can be found at http://django-stripe-payments.readthedocs.org
The Pinax documentation is available at http://pinaxproject.com/pinax/.


## Code of Conduct

In order to foster a kind, inclusive, and harassment-free community, the Pinax Project has a code of conduct, which can be found here http://pinaxproject.com/pinax/code_of_conduct/.


## Pinax Project Blog and Twitter

For updates and news regarding the Pinax Project, please follow us on Twitter at @pinaxproject and check out our blog http://blog.pinaxproject.com.
