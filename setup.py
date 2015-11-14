import codecs

from os import path
from setuptools import find_packages, setup


def read(*parts):
    filename = path.join(path.dirname(__file__), *parts)
    with codecs.open(filename, encoding="utf-8") as fp:
        return fp.read()


NAME = "pinax-stripe"
DESCRIPTION = "a payments Django app for Stripe"
AUTHOR = "Pinax Team"
AUTHOR_EMAIL = "team@pinaxproject.com"
URL = "https://github.com/pinax/pinax-stripe"


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
        "pinax.stripe": [
            "templates/pinax/stripe/email/body_base.txt",
            "templates/pinax/stripe/email/body.txt",
            "templates/pinax/stripe/email/subject.txt",
            "templates/pinax/stripe/_cancel_form.html",
            "templates/pinax/stripe/_change_card_form.html",
            "templates/pinax/stripe/_change_plan_form.html",
            "templates/pinax/stripe/_subscribe_form.html",
            "templates/pinax/stripe/_subscription_status.html",
            "templates/pinax/stripe/base.html",
            "templates/pinax/stripe/cancel.html",
            "templates/pinax/stripe/change_card.html",
            "templates/pinax/stripe/change_plan.html",
            "templates/pinax/stripe/history.html",
            "templates/pinax/stripe/subscribe.html",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2"
        "Programming Language :: Python :: 3",
        "Framework :: Django",
    ],
    install_requires=[
        "django-appconf>=1.0.1",
        "django-eldarion-ajax>=0.1",
        "django-jsonfield>=0.9.15",
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
