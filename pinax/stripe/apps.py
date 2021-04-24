import importlib

from django.apps import AppConfig as BaseAppConfig
from django.utils.translation import gettext_lazy as _


class AppConfig(BaseAppConfig):

    name = "pinax.stripe"
    label = "pinax_stripe"
    verbose_name = _("Pinax Stripe")

    def ready(self):
        importlib.import_module("pinax.stripe.webhooks")
