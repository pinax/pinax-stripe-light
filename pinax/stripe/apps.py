from django.apps import AppConfig as BaseAppConfig
from django.utils.translation import ugettext_lazy as _


class AppConfig(BaseAppConfig):

    name = "pinax.stripe"
    label = "pinax_stripe"
    verbose_name = _("Pinax Stripe")
