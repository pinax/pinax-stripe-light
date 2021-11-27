from django.conf import settings  # noqa

import stripe
from appconf import AppConf

from pinax.stripe import __version__


class PinaxStripeAppConf(AppConf):

    PUBLIC_KEY = None
    SECRET_KEY = None
    API_VERSION = "2020-08-27"
    ENDPOINT_SECRET = None

    class Meta:
        prefix = "pinax_stripe"
        required = ["PUBLIC_KEY", "SECRET_KEY", "API_VERSION", "ENDPOINT_SECRET"]

    def configure_api_version(self, value):
        stripe.api_version = value
        return value

    def configure_secret_key(self, value):
        stripe.api_key = value
        return value

    def configure(self):
        stripe.set_app_info(
            name="Pinax Stripe Light",
            version=__version__,
            url="https://github.com/pinax/pinax-stripe-light"
        )
        return self.configured_data
