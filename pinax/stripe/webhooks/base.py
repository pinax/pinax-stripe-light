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
