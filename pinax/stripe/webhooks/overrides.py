import stripe

from ..conf import settings
from ..utils import obfuscate_secret_key
from .generated import AccountApplicationDeauthorizedWebhook


class CustomAccountApplicationDeauthorizedWebhook(AccountApplicationDeauthorizedWebhook):

    def validate(self):
        """
        Specialized validation of incoming events.

        When this event is for a connected account we should not be able to
        fetch the event anymore (since we have been disconnected).
        But there might be multiple connections (e.g. for Dev/Prod).

        Therefore we try to retrieve the event, and handle a
        PermissionError exception to be expected (since we cannot access the
        account anymore).
        """
        try:
            super().validate()
        except stripe.error.PermissionError as exc:
            if self.stripe_account:
                if self.stripe_account not in str(exc) and obfuscate_secret_key(settings.PINAX_STRIPE_SECRET_KEY) not in str(exc):
                    raise exc
            self.event.valid = True
            self.event.validated_message = self.event.webhook_message
