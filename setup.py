import codecs

from os import path
from setuptools import find_packages, setup


def read(*parts):
    filename = path.join(path.dirname(__file__), *parts)
    with codecs.open(filename, encoding="utf-8") as fp:
        return fp.read()


PACKAGE = "payments"
NAME = "django-stripe-payments"
DESCRIPTION = "a payments Django app for Stripe"
AUTHOR = "Pinax Team"
AUTHOR_EMAIL = "team@pinaxproject.com"
URL = "https://github.com/pinax/django-stripe-payments"


setup(
    name=NAME,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=read("README.rst"),
    version="2.0.0",
    license="MIT",
    url=URL,
    packages=find_packages(),
    package_data={
        "payments": [
            "templates/payments/email/body_base.txt",
            "templates/payments/email/body.txt",
            "templates/payments/email/subject.txt",
            "templates/payments/_cancel_form.html",
            "templates/payments/_change_card_form.html",
            "templates/payments/_change_plan_form.html",
            "templates/payments/_subscribe_form.html",
            "templates/payments/_subscription_status.html",
            "templates/payments/base.html",
            "templates/payments/cancel.html",
            "templates/payments/change_card.html",
            "templates/payments/change_plan.html",
            "templates/payments/history.html",
            "templates/payments/subscribe.html",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Framework :: Django",
    ],
    install_requires=[
        "django-jsonfield>=0.8",
        "stripe>=1.7.9",
        "django>=1.6",
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
