#!/bin/bash
set -euo pipefail

DJANGO_SETTINGS_MODULE=pinax.stripe.tests.settings

python -m pytest --cov --cov-report=term-missing:skip-covered pinax
