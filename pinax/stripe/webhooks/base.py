import json
import sys
import traceback

import stripe

from .. import models
from .registry import registry


class Registerable(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(Registerable, cls).__new__(cls, clsname, bases, attrs)
        if getattr(newclass, "name", None) is not None:
            registry.register(newclass)
        return newclass


class Webhook(metaclass=Registerable):

    name = None

    def __init__(self, event):
        if event.kind != self.name:
            raise Exception("The Webhook handler ({}) received the wrong type of Event ({})".format(self.name, event.kind))
        self.event = event
        self.stripe_account = None

    def validate(self):
        """
        Validate incoming events.

        We fetch the event data to ensure it is legit.
        For Connect accounts we must fetch the event using the `stripe_account`
        parameter.
        """
        self.stripe_account = self.event.webhook_message.get("account", None)
        evt = stripe.Event.retrieve(
            self.event.stripe_id,
            stripe_account=self.stripe_account
        )
        self.event.validated_message = json.loads(
            json.dumps(
                evt.to_dict(),
                sort_keys=True,
            )
        )
        self.event.valid = self.is_event_valid(self.event.webhook_message["data"], self.event.validated_message["data"])
        self.event.save()

    @staticmethod
    def is_event_valid(webhook_message_data, validated_message_data):
        """
        Notice "data" may contain a "previous_attributes" section
        """
        return "object" in webhook_message_data and "object" in validated_message_data and \
               webhook_message_data["object"] == validated_message_data["object"]

    def send_signal(self):
        signal = registry.get_signal(self.name)
        if signal:
            return signal.send(sender=self.__class__, event=self.event)

    def log_exception(self, data, exception):
        info = sys.exc_info()
        info_formatted = "".join(traceback.format_exception(*info)) if info[1] is not None else ""
        models.EventProcessingException.objects.create(
            event=self.event,
            data=data or "",
            message=str(exception),
            traceback=info_formatted
        )

    def process(self):
        if self.event.processed:
            return
        self.validate()
        if not self.event.valid:
            return

        try:
            self.process_webhook()
            self.send_signal()
            self.event.processed = True
            self.event.save()
        except Exception as e:
            data = None
            if isinstance(e, stripe.error.StripeError):
                data = e.http_body
            self.log_exception(data=data, exception=e)
            raise e

    def process_webhook(self):
        return
