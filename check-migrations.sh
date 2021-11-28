#!/bin/bash
set -euo pipefail

export DJANGO_SETTINGS_MODULE=pinax.stripe.tests.settings

django-admin makemigrations --check -v3 --dry-run --noinput pinax_stripe
