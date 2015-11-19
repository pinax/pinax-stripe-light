import json

import stripe

from .. import models
from .. import signals

from .customers import CustomerProxy
from .exceptions import EventProcessingExceptionProxy
from .subscriptions import SubscriptionProxy
from .transfers import TransferProxy


class EventProxy(models.Event):

    class Meta:
        proxy = True

    @property
    def message(self):
        return self.validated_message

    def link_customer(self):
        cus_id = None
        customer_crud_events = [
            "customer.created",
            "customer.updated",
            "customer.deleted"
        ]
        if self.kind in customer_crud_events:
            cus_id = self.message["data"]["object"]["id"]
        else:
            cus_id = self.message["data"]["object"].get("customer", None)

        if cus_id is not None:
            try:
                self.customer = CustomerProxy.objects.get(stripe_id=cus_id)
                self.save()
            except models.Customer.DoesNotExist:
                pass

    def validate(self):
        evt = stripe.Event.retrieve(self.stripe_id)
        self.validated_message = json.loads(
            json.dumps(
                evt.to_dict(),
                sort_keys=True,
                cls=stripe.StripeObjectEncoder
            )
        )
        self.valid = self.webhook_message["data"] == self.validated_message["data"]
        self.save()

    def process(self):  # @@@ to complex, fix later  # noqa
        if not self.valid or self.processed:
            return
        try:
            if not self.kind.startswith("plan.") and not self.kind.startswith("transfer."):
                self.link_customer()
            if self.kind.startswith("invoice."):
                signals.invoice_event_received.send(sender=EventProxy, event=self)
            elif self.kind.startswith("charge."):
                signals.charge_event_received.send(sender=EventProxy, event=self)
            elif self.kind.startswith("transfer."):
                TransferProxy.process_transfer(
                    self,
                    self.message["data"]["object"]
                )
            elif self.kind.startswith("customer.subscription."):
                if self.kind == "customer.subscription.deleted":
                    sub = next(iter(SubscriptionProxy.objects.filter(stripe_id=self.validated_message["data"]["object"]["id"])), None)
                    if sub is not None:
                        sub.delete()
                if self.customer:
                    signals.customer_subscription_event.send(sender=EventProxy, event=self, customer=self.customer)
            elif self.kind == "customer.deleted":
                self.customer.purge()
            self.send_signal()
            self.processed = True
            self.save()
        except stripe.StripeError as e:
            EventProcessingExceptionProxy.log(
                data=e.http_body,
                exception=e,
                event=self
            )
            signals.webhook_processing_error.send(
                sender=EventProxy,
                data=e.http_body,
                exception=e
            )

    def send_signal(self):
        signal = signals.WEBHOOK_SIGNALS.get(self.kind)
        if signal:
            return signal.send(sender=EventProxy, event=self)
