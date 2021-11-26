import json
import sys
import traceback

from django.dispatch import Signal

import stripe

from . import models
from .conf import settings
from .utils import obfuscate_secret_key


class WebhookRegistry:

    def __init__(self):
        self._registry = {}

    def register(self, webhook):
        self._registry[webhook.name] = {
            "webhook": webhook,
            "signal": Signal()
        }

    def keys(self):
        return self._registry.keys()

    def get(self, name):
        return self[name]["webhook"]

    def get_signal(self, name, default=None):
        try:
            return self[name]["signal"]
        except KeyError:
            return default

    def signals(self):
        return {
            key: self.get_signal(key)
            for key in self.keys()
        }

    def __getitem__(self, name):
        return self._registry[name]


registry = WebhookRegistry()
del WebhookRegistry


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


class AccountUpdatedWebhook(Webhook):
    name = "account.updated"
    description = "Occurs whenever an account status or property has changed."


class AccountApplicationDeauthorizeWebhook(Webhook):
    name = "account.application.deauthorized"
    description = "Occurs whenever a user deauthorizes an application. Sent to the related application only."

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


# @@@ with signals not sure we need all these

class AccountExternalAccountCreatedWebhook(Webhook):
    name = "account.external_account.created"
    description = "Occurs whenever an external account is created."


class AccountExternalAccountDeletedWebhook(Webhook):
    name = "account.external_account.deleted"
    description = "Occurs whenever an external account is deleted."


class AccountExternalAccountUpdatedWebhook(Webhook):
    name = "account.external_account.updated"
    description = "Occurs whenever an external account is updated."


class ApplicationFeeCreatedWebhook(Webhook):
    name = "application_fee.created"
    description = "Occurs whenever an application fee is created on a charge."


class ApplicationFeeRefundedWebhook(Webhook):
    name = "application_fee.refunded"
    description = "Occurs whenever an application fee is refunded, whether from refunding a charge or from refunding the application fee directly, including partial refunds."


class ApplicationFeeRefundUpdatedWebhook(Webhook):
    name = "application_fee.refund.updated"
    description = "Occurs whenever an application fee refund is updated."


class BalanceAvailableWebhook(Webhook):
    name = "balance.available"
    description = "Occurs whenever your Stripe balance has been updated (e.g. when a charge collected is available to be paid out). By default, Stripe will automatically transfer any funds in your balance to your bank account on a daily basis."


class BitcoinReceiverCreatedWebhook(Webhook):
    name = "bitcoin.receiver.created"
    description = "Occurs whenever a receiver has been created."


class BitcoinReceiverFilledWebhook(Webhook):
    name = "bitcoin.receiver.filled"
    description = "Occurs whenever a receiver is filled (that is, when it has received enough bitcoin to process a payment of the same amount)."


class BitcoinReceiverUpdatedWebhook(Webhook):
    name = "bitcoin.receiver.updated"
    description = "Occurs whenever a receiver is updated."


class BitcoinReceiverTransactionCreatedWebhook(Webhook):
    name = "bitcoin.receiver.transaction.created"
    description = "Occurs whenever bitcoin is pushed to a receiver."


class ChargeCapturedWebhook(Webhook):
    name = "charge.captured"
    description = "Occurs whenever a previously uncaptured charge is captured."


class ChargeFailedWebhook(Webhook):
    name = "charge.failed"
    description = "Occurs whenever a failed charge attempt occurs."


class ChargeRefundedWebhook(Webhook):
    name = "charge.refunded"
    description = "Occurs whenever a charge is refunded, including partial refunds."


class ChargeSucceededWebhook(Webhook):
    name = "charge.succeeded"
    description = "Occurs whenever a new charge is created and is successful."


class ChargeUpdatedWebhook(Webhook):
    name = "charge.updated"
    description = "Occurs whenever a charge description or metadata is updated."


class ChargeDisputeClosedWebhook(Webhook):
    name = "charge.dispute.closed"
    description = "Occurs when the dispute is resolved and the dispute status changes to won or lost."


class ChargeDisputeCreatedWebhook(Webhook):
    name = "charge.dispute.created"
    description = "Occurs whenever a customer disputes a charge with their bank (chargeback)."


class ChargeDisputeFundsReinstatedWebhook(Webhook):
    name = "charge.dispute.funds_reinstated"
    description = "Occurs when funds are reinstated to your account after a dispute is won."


class ChargeDisputeFundsWithdrawnWebhook(Webhook):
    name = "charge.dispute.funds_withdrawn"
    description = "Occurs when funds are removed from your account due to a dispute."


class ChargeDisputeUpdatedWebhook(Webhook):
    name = "charge.dispute.updated"
    description = "Occurs when the dispute is updated (usually with evidence)."


class CouponCreatedWebhook(Webhook):
    name = "coupon.created"
    description = "Occurs whenever a coupon is created."


class CouponDeletedWebhook(Webhook):
    name = "coupon.deleted"
    description = "Occurs whenever a coupon is deleted."


class CouponUpdatedWebhook(Webhook):
    name = "coupon.updated"
    description = "Occurs whenever a coupon is updated."


class CustomerCreatedWebhook(Webhook):
    name = "customer.created"
    description = "Occurs whenever a new customer is created."


class CustomerDeletedWebhook(Webhook):
    name = "customer.deleted"
    description = "Occurs whenever a customer is deleted."


class CustomerUpdatedWebhook(Webhook):
    name = "customer.updated"
    description = "Occurs whenever any property of a customer changes."


class CustomerDiscountCreatedWebhook(Webhook):
    name = "customer.discount.created"
    description = "Occurs whenever a coupon is attached to a customer."


class CustomerDiscountDeletedWebhook(Webhook):
    name = "customer.discount.deleted"
    description = "Occurs whenever a customer's discount is removed."


class CustomerDiscountUpdatedWebhook(Webhook):
    name = "customer.discount.updated"
    description = "Occurs whenever a customer is switched from one coupon to another."


class CustomerSourceCreatedWebhook(Webhook):
    name = "customer.source.created"
    description = "Occurs whenever a new source is created for the customer."


class CustomerSourceDeletedWebhook(Webhook):
    name = "customer.source.deleted"
    description = "Occurs whenever a source is removed from a customer."


class CustomerSourceUpdatedWebhook(Webhook):
    name = "customer.source.updated"
    description = "Occurs whenever a source's details are changed."


class CustomerSubscriptionCreatedWebhook(Webhook):
    name = "customer.subscription.created"
    description = "Occurs whenever a customer with no subscription is signed up for a plan."


class CustomerSubscriptionDeletedWebhook(Webhook):
    name = "customer.subscription.deleted"
    description = "Occurs whenever a customer ends their subscription."


class CustomerSubscriptionTrialWillEndWebhook(Webhook):
    name = "customer.subscription.trial_will_end"
    description = "Occurs three days before the trial period of a subscription is scheduled to end."


class CustomerSubscriptionUpdatedWebhook(Webhook):
    name = "customer.subscription.updated"
    description = "Occurs whenever a subscription changes. Examples would include switching from one plan to another, or switching status from trial to active."


class InvoiceCreatedWebhook(Webhook):
    name = "invoice.created"
    description = "Occurs whenever a new invoice is created. If you are using webhooks, Stripe will wait one hour after they have all succeeded to attempt to pay the invoice; the only exception here is on the first invoice, which gets created and paid immediately when you subscribe a customer to a plan. If your webhooks do not all respond successfully, Stripe will continue retrying the webhooks every hour and will not attempt to pay the invoice. After 3 days, Stripe will attempt to pay the invoice regardless of whether or not your webhooks have succeeded. See how to respond to a webhook."


class InvoicePaymentFailedWebhook(Webhook):
    name = "invoice.payment_failed"
    description = "Occurs whenever an invoice attempts to be paid, and the payment fails. This can occur either due to a declined payment, or because the customer has no active card. A particular case of note is that if a customer with no active card reaches the end of its free trial, an invoice.payment_failed notification will occur."


class InvoicePaymentSucceededWebhook(Webhook):
    name = "invoice.payment_succeeded"
    description = "Occurs whenever an invoice attempts to be paid, and the payment succeeds."


class InvoiceUpdatedWebhook(Webhook):
    name = "invoice.updated"
    description = "Occurs whenever an invoice changes (for example, the amount could change)."


class InvoiceItemCreatedWebhook(Webhook):
    name = "invoiceitem.created"
    description = "Occurs whenever an invoice item is created."


class InvoiceItemDeletedWebhook(Webhook):
    name = "invoiceitem.deleted"
    description = "Occurs whenever an invoice item is deleted."


class InvoiceItemUpdatedWebhook(Webhook):
    name = "invoiceitem.updated"
    description = "Occurs whenever an invoice item is updated."


class OrderCreatedWebhook(Webhook):
    name = "order.created"
    description = "Occurs whenever an order is created."


class OrderPaymentFailedWebhook(Webhook):
    name = "order.payment_failed"
    description = "Occurs whenever payment is attempted on an order, and the payment fails."


class OrderPaymentSucceededWebhook(Webhook):
    name = "order.payment_succeeded"
    description = "Occurs whenever payment is attempted on an order, and the payment succeeds."


class OrderUpdatedWebhook(Webhook):
    name = "order.updated"
    description = "Occurs whenever an order is updated."


class PaymentCreatedWebhook(Webhook):
    name = "payment.created"
    description = "A payment has been received by a Connect account via Transfer from the platform account."


class PlanCreatedWebhook(Webhook):
    name = "plan.created"
    description = "Occurs whenever a plan is created."


class PlanDeletedWebhook(Webhook):
    name = "plan.deleted"
    description = "Occurs whenever a plan is deleted."


class PlanUpdatedWebhook(Webhook):
    name = "plan.updated"
    description = "Occurs whenever a plan is updated."


class ProductCreatedWebhook(Webhook):
    name = "product.created"
    description = "Occurs whenever a product is created."


class ProductUpdatedWebhook(Webhook):
    name = "product.updated"
    description = "Occurs whenever a product is updated."


class RecipientCreatedWebhook(Webhook):
    name = "recipient.created"
    description = "Occurs whenever a recipient is created."


class RecipientDeletedWebhook(Webhook):
    name = "recipient.deleted"
    description = "Occurs whenever a recipient is deleted."


class RecipientUpdatedWebhook(Webhook):
    name = "recipient.updated"
    description = "Occurs whenever a recipient is updated."


class SKUCreatedWebhook(Webhook):
    name = "sku.created"
    description = "Occurs whenever a SKU is created."


class SKUUpdatedWebhook(Webhook):
    name = "sku.updated"
    description = "Occurs whenever a SKU is updated."


class TransferCreatedWebhook(Webhook):
    name = "transfer.created"
    description = "Occurs whenever a new transfer is created."


class TransferFailedWebhook(Webhook):
    name = "transfer.failed"
    description = "Occurs whenever Stripe attempts to send a transfer and that transfer fails."


class TransferPaidWebhook(Webhook):
    name = "transfer.paid"
    description = "Occurs whenever a sent transfer is expected to be available in the destination bank account. If the transfer failed, a transfer.failed webhook will additionally be sent at a later time. Note to Connect users: this event is only created for transfers from your connected Stripe accounts to their bank accounts, not for transfers to the connected accounts themselves."


class TransferReversedWebhook(Webhook):
    name = "transfer.reversed"
    description = "Occurs whenever a transfer is reversed, including partial reversals."


class TransferUpdatedWebhook(Webhook):
    name = "transfer.updated"
    description = "Occurs whenever the description or metadata of a transfer is updated."


class PingWebhook(Webhook):
    name = "ping"
    description = "May be sent by Stripe at any time to see if a provided webhook URL is working."
