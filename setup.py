from setuptools import find_packages, setup


NAME = "pinax-stripe"
DESCRIPTION = "a payments Django app for Stripe"
AUTHOR = "Pinax Team"
AUTHOR_EMAIL = "team@pinaxproject.com"
URL = "https://github.com/pinax/pinax-stripe"
LONG_DESCRIPTION = """
============
Pinax Stripe
============

.. image:: http://slack.pinaxproject.com/badge.svg
    :target: http://slack.pinaxproject.com/

.. image:: https://img.shields.io/travis/pinax/pinax-stripe.svg
    :target: https://travis-ci.org/pinax/pinax-stripe

.. image:: https://img.shields.io/coveralls/pinax/pinax-stripe.svg
    :target: https://coveralls.io/r/pinax/pinax-stripe

.. image:: https://img.shields.io/pypi/dm/pinax-stripe.svg
    :target:  https://pypi.python.org/pypi/pinax-stripe/

.. image:: https://img.shields.io/pypi/v/pinax-stripe.svg
    :target:  https://pypi.python.org/pypi/pinax-stripe/

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target:  https://pypi.python.org/pypi/pinax-stripe/


This app was formerly called ``django-stripe-payments`` and has been renamed to
avoid namespace collisions and to have more consistancy with Pinax.

Pinax
------

Pinax is an open-source platform built on the Django Web Framework. It is an
ecosystem of reusable Django apps, themes, and starter project templates.
This collection can be found at http://pinaxproject.com.

This app was developed as part of the Pinax ecosystem but is just a Django app
and can be used independently of other Pinax apps.


pinax-stripe
------------

``pinax-stripe`` is a payments Django app for Stripe.

This app allows you to process one off charges as well as signup users for
recurring subscriptions managed by Stripe.
"""

setup(
    name=NAME,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    version="3.3.0",
    license="MIT",
    url=URL,
    packages=find_packages(),
    package_data={
        "pinax.stripe": [
            "templates/pinax/stripe/email/body_base.txt",
            "templates/pinax/stripe/email/body.txt",
            "templates/pinax/stripe/email/subject.txt"
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ],
    install_requires=[
        "django-appconf>=1.0.1",
        "jsonfield>=1.0.3",
        "stripe>=1.7.9",
        "django>=1.7",
        "pytz",
        "six",
    ],
    test_suite="runtests.runtests",
    tests_require=[
        "mock",
        "django_forms_bootstrap",
    ],
    zip_safe=False,
)
