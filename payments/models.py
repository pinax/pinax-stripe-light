import datetime
import decimal
import json
import traceback

import six
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.utils import timezone
from django.utils.encoding import smart_str
from django.template.loader import render_to_string

from django.contrib.sites.models import Site

import stripe

from jsonfield.fields import JSONField

from .managers import CustomerManager, ChargeManager, TransferManager
from .settings import (
    DEFAULT_PLAN,
    INVOICE_FROM_EMAIL,
    PAYMENTS_PLANS,
    plan_from_stripe_id,
    SEND_EMAIL_RECEIPTS,
    TRIAL_PERIOD_FOR_USER_CALLBACK,
    PLAN_QUANTITY_CALLBACK
)
from .signals import (
    cancelled,
    card_changed,
    subscription_made,
    webhook_processing_error,
    WEBHOOK_SIGNALS,
)
from .utils import (
    convert_tstamp,
    convert_amount_for_db,
    convert_amount_for_api,
)


stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", "2012-11-07")


class StripeObject(models.Model):

    stripe_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:  # pylint: disable=E0012,C1001
        abstract = True


class EventProcessingException(models.Model):

    event = models.ForeignKey("Event", null=True)
    data = models.TextField()
    message = models.CharField(max_length=500)
    traceback = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    @classmethod
    def log(cls, data, exception, event):
        cls.objects.create(
            event=event,
            data=data or "",
            message=str(exception),
            traceback=traceback.format_exc()
        )

    def __unicode__(self):
        return six.u("<{}, pk={}, Event={}>").format(self.message, self.pk, self.event)


class Event(StripeObject):

    kind = models.CharField(max_length=250)
    livemode = models.BooleanField(default=False)
    customer = models.ForeignKey("Customer", null=True)
    webhook_message = JSONField()
    validated_message = JSONField(null=True)
    valid = models.NullBooleanField(null=True)
    processed = models.BooleanField(default=False)

    @property
    def message(self):
        return self.validated_message

    def __unicode__(self):
        return "%s - %s" % (self.kind, self.stripe_id)

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
                self.customer = Customer.objects.get(stripe_id=cus_id)
                self.save()
            except Customer.DoesNotExist:
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
        if self.webhook_message["data"] == self.validated_message["data"]:
            self.valid = True
        else:
            self.valid = False
        self.save()

    def process(self):  # @@@ to complex, fix later  # noqa
        """
            "account.updated",
            "account.application.deauthorized",
            "charge.succeeded",
            "charge.failed",
            "charge.refunded",
            "charge.dispute.created",
            "charge.dispute.updated",
            "chagne.dispute.closed",
            "customer.created",
            "customer.updated",
            "customer.deleted",
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "customer.subscription.trial_will_end",
            "customer.discount.created",
            "customer.discount.updated",
            "customer.discount.deleted",
            "invoice.created",
            "invoice.updated",
            "invoice.payment_succeeded",
            "invoice.payment_failed",
            "invoiceitem.created",
            "invoiceitem.updated",
            "invoiceitem.deleted",
            "plan.created",
            "plan.updated",
            "plan.deleted",
            "coupon.created",
            "coupon.updated",
            "coupon.deleted",
            "transfer.created",
            "transfer.updated",
            "transfer.failed",
            "ping"
        """
        if not self.valid or self.processed:
            return
        try:
            if not self.kind.startswith("plan.") and not self.kind.startswith("transfer."):
                self.link_customer()
            if self.kind.startswith("invoice."):
                Invoice.handle_event(self)
            elif self.kind.startswith("charge."):
                self.customer.record_charge(
                    self.message["data"]["object"]["id"]
                )
            elif self.kind.startswith("transfer."):
                Transfer.process_transfer(
                    self,
                    self.message["data"]["object"]
                )
            elif self.kind.startswith("customer.subscription."):
                if self.customer:
                    self.customer.sync_current_subscription()
            elif self.kind == "customer.deleted":
                self.customer.purge()
            self.send_signal()
            self.processed = True
            self.save()
        except stripe.StripeError as e:
            EventProcessingException.log(
                data=e.http_body,
                exception=e,
                event=self
            )
            webhook_processing_error.send(
                sender=Event,
                data=e.http_body,
                exception=e
            )

    def send_signal(self):
        signal = WEBHOOK_SIGNALS.get(self.kind)
        if signal:
            return signal.send(sender=Event, event=self)


class Transfer(StripeObject):
    # pylint: disable=C0301
    event = models.ForeignKey(Event, related_name="transfers")
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=25, default="usd")
    status = models.CharField(max_length=25)
    date = models.DateTimeField()
    description = models.TextField(null=True, blank=True)
    adjustment_count = models.IntegerField(null=True)
    adjustment_fees = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    adjustment_gross = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    charge_count = models.IntegerField(null=True)
    charge_fees = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    charge_gross = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    collected_fee_count = models.IntegerField(null=True)
    collected_fee_gross = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    net = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    refund_count = models.IntegerField(null=True)
    refund_fees = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    refund_gross = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    validation_count = models.IntegerField(null=True)
    validation_fees = models.DecimalField(decimal_places=2, max_digits=9, null=True)

    objects = TransferManager()

    def update_status(self):
        self.status = stripe.Transfer.retrieve(self.stripe_id).status
        self.save()

    @classmethod
    def process_transfer(cls, event, transfer):
        defaults = {
            "amount": convert_amount_for_db(transfer["amount"], transfer["currency"]),
            "currency": transfer["currency"],
            "status": transfer["status"],
            "date": convert_tstamp(transfer, "date"),
            "description": transfer.get("description", "")
        }
        summary = transfer.get("summary")
        if summary:
            defaults.update({
                "adjustment_count": summary.get("adjustment_count"),
                "adjustment_fees": summary.get("adjustment_fees"),
                "adjustment_gross": summary.get("adjustment_gross"),
                "charge_count": summary.get("charge_count"),
                "charge_fees": summary.get("charge_fees"),
                "charge_gross": summary.get("charge_gross"),
                "collected_fee_count": summary.get("collected_fee_count"),
                "collected_fee_gross": summary.get("collected_fee_gross"),
                "refund_count": summary.get("refund_count"),
                "refund_fees": summary.get("refund_fees"),
                "refund_gross": summary.get("refund_gross"),
                "validation_count": summary.get("validation_count"),
                "validation_fees": summary.get("validation_fees"),
                "net": convert_amount_for_db(summary.get("net"), transfer["currency"]),
            })
        for field in defaults:
            if field.endswith("fees") or field.endswith("gross"):
                defaults[field] = convert_amount_for_db(defaults[field])  # assume in usd only
        if event.kind == "transfer.paid":
            defaults.update({"event": event})
            obj, created = Transfer.objects.get_or_create(
                stripe_id=transfer["id"],
                defaults=defaults
            )
        else:
            obj, created = Transfer.objects.get_or_create(
                stripe_id=transfer["id"],
                event=event,
                defaults=defaults
            )
        if created and summary:
            for fee in summary.get("charge_fee_details", []):
                obj.charge_fee_details.create(
                    amount=convert_amount_for_db(fee["amount"], fee["currency"]),
                    currency=fee["currency"],
                    application=fee.get("application", ""),
                    description=fee.get("description", ""),
                    kind=fee["type"]
                )
        else:
            obj.status = transfer["status"]
            obj.save()
        if event.kind == "transfer.updated":
            obj.update_status()


class TransferChargeFee(models.Model):

    transfer = models.ForeignKey(Transfer, related_name="charge_fee_details")
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    application = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    kind = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)


class Customer(StripeObject):

    user = models.OneToOneField(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        null=True
    )
    card_fingerprint = models.CharField(max_length=200, blank=True)
    card_last_4 = models.CharField(max_length=4, blank=True)
    card_kind = models.CharField(max_length=50, blank=True)
    date_purged = models.DateTimeField(null=True, editable=False)

    objects = CustomerManager()

    def __unicode__(self):
        return smart_str(self.user)

    @property
    def stripe_customer(self):
        return stripe.Customer.retrieve(self.stripe_id)

    def purge(self):
        try:
            self.stripe_customer.delete()
        except stripe.InvalidRequestError as e:
            if smart_str(e).startswith("No such customer:"):
                # The exception was thrown because the customer was already
                # deleted on the stripe side, ignore the exception
                pass
            else:
                # The exception was raised for another reason, re-raise it
                raise
        self.user = None
        self.card_fingerprint = ""
        self.card_last_4 = ""
        self.card_kind = ""
        self.date_purged = timezone.now()
        self.save()

    def delete(self, using=None):
        # Only way to delete a customer is to use SQL
        self.purge()

    def can_charge(self):
        return self.card_fingerprint and \
            self.card_last_4 and \
            self.card_kind and \
            self.date_purged is None

    def has_active_subscription(self):
        try:
            return self.current_subscription.is_valid()
        except CurrentSubscription.DoesNotExist:
            return False

    def cancel(self, at_period_end=True):
        try:
            current = self.current_subscription
        except CurrentSubscription.DoesNotExist:
            return
        sub = self.stripe_customer.cancel_subscription(
            at_period_end=at_period_end
        )
        current.status = sub.status
        current.cancel_at_period_end = sub.cancel_at_period_end
        current.current_period_end = convert_tstamp(sub, "current_period_end")
        current.save()
        cancelled.send(sender=self, stripe_response=sub)

    @classmethod
    def create(cls, user, card=None, plan=None, charge_immediately=True):

        if card and plan:
            plan = PAYMENTS_PLANS[plan]["stripe_plan_id"]
        elif DEFAULT_PLAN:
            plan = PAYMENTS_PLANS[DEFAULT_PLAN]["stripe_plan_id"]
        else:
            plan = None

        trial_end = None
        if TRIAL_PERIOD_FOR_USER_CALLBACK and plan:
            trial_days = TRIAL_PERIOD_FOR_USER_CALLBACK(user)
            trial_end = datetime.datetime.utcnow() + datetime.timedelta(
                days=trial_days
            )

        stripe_customer = stripe.Customer.create(
            email=user.email,
            card=card,
            plan=plan or DEFAULT_PLAN,
            trial_end=trial_end
        )

        if stripe_customer.active_card:
            cus = cls.objects.create(
                user=user,
                stripe_id=stripe_customer.id,
                card_fingerprint=stripe_customer.active_card.fingerprint,
                card_last_4=stripe_customer.active_card.last4,
                card_kind=stripe_customer.active_card.type
            )
        else:
            cus = cls.objects.create(
                user=user,
                stripe_id=stripe_customer.id,
            )

        if plan:
            if stripe_customer.subscription:
                cus.sync_current_subscription(cu=stripe_customer)
            if charge_immediately:
                cus.send_invoice()

        return cus

    def update_card(self, token):
        cu = self.stripe_customer
        cu.card = token
        cu.save()
        self.save_card(cu)

    def save_card(self, cu=None):
        cu = cu or self.stripe_customer
        active_card = cu.active_card
        self.card_fingerprint = active_card.fingerprint
        self.card_last_4 = active_card.last4
        self.card_kind = active_card.type
        self.save()
        card_changed.send(sender=self, stripe_response=cu)

    def retry_unpaid_invoices(self):
        self.sync_invoices()
        for inv in self.invoices.filter(paid=False, closed=False):
            try:
                inv.retry()  # Always retry unpaid invoices
            except stripe.InvalidRequestError as error:
                if smart_str(error) != "Invoice is already paid":
                    raise error

    def send_invoice(self):
        try:
            invoice = stripe.Invoice.create(customer=self.stripe_id)
            if invoice.amount_due > 0:
                invoice.pay()
            return True
        except stripe.InvalidRequestError:
            return False  # There was nothing to invoice

    def sync(self, cu=None):
        cu = cu or self.stripe_customer
        updated = False
        if hasattr(cu, "active_card") and cu.active_card:
            # Test to make sure the card has changed, otherwise do not update it
            # (i.e. refrain from sending any signals)
            if (self.card_last_4 != cu.active_card.last4 or
                    self.card_fingerprint != cu.active_card.fingerprint or
                    self.card_kind != cu.active_card.type):
                updated = True
                self.card_last_4 = cu.active_card.last4
                self.card_fingerprint = cu.active_card.fingerprint
                self.card_kind = cu.active_card.type
        else:
            updated = True
            self.card_fingerprint = ""
            self.card_last_4 = ""
            self.card_kind = ""

        if updated:
            self.save()
            card_changed.send(sender=self, stripe_response=cu)

    def sync_invoices(self, cu=None):
        cu = cu or self.stripe_customer
        for invoice in cu.invoices().data:
            Invoice.sync_from_stripe_data(invoice, send_receipt=False)

    def sync_charges(self, cu=None):
        cu = cu or self.stripe_customer
        for charge in cu.charges().data:
            self.record_charge(charge.id)

    def sync_current_subscription(self, cu=None):
        cu = cu or self.stripe_customer
        sub = getattr(cu, "subscription", None)
        if sub is None:
            try:
                self.current_subscription.delete()
            except CurrentSubscription.DoesNotExist:
                pass
        else:
            try:
                sub_obj = self.current_subscription
                sub_obj.plan = plan_from_stripe_id(sub.plan.id)
                sub_obj.current_period_start = convert_tstamp(
                    sub.current_period_start
                )
                sub_obj.current_period_end = convert_tstamp(
                    sub.current_period_end
                )
                sub_obj.amount = convert_amount_for_db(sub.plan.amount, sub.plan.currency)
                sub_obj.currency = sub.plan.currency
                sub_obj.status = sub.status
                sub_obj.cancel_at_period_end = sub.cancel_at_period_end
                sub_obj.start = convert_tstamp(sub.start)
                sub_obj.quantity = sub.quantity
                sub_obj.save()
            except CurrentSubscription.DoesNotExist:
                sub_obj = CurrentSubscription.objects.create(
                    customer=self,
                    plan=plan_from_stripe_id(sub.plan.id),
                    current_period_start=convert_tstamp(
                        sub.current_period_start
                    ),
                    current_period_end=convert_tstamp(
                        sub.current_period_end
                    ),
                    amount=convert_amount_for_db(sub.plan.amount, sub.plan.currency),
                    currency=sub.plan.currency,
                    status=sub.status,
                    cancel_at_period_end=sub.cancel_at_period_end,
                    start=convert_tstamp(sub.start),
                    quantity=sub.quantity
                )

            if sub.trial_start and sub.trial_end:
                sub_obj.trial_start = convert_tstamp(sub.trial_start)
                sub_obj.trial_end = convert_tstamp(sub.trial_end)
                sub_obj.save()

            return sub_obj

    def update_plan_quantity(self, quantity, charge_immediately=False):
        self.subscribe(
            plan=plan_from_stripe_id(
                self.stripe_customer.subscription.plan.id
            ),
            quantity=quantity,
            charge_immediately=charge_immediately
        )

    def subscribe(self, plan, quantity=None, trial_days=None,
                  charge_immediately=True, token=None, coupon=None):
        if quantity is None:
            if PLAN_QUANTITY_CALLBACK is not None:
                quantity = PLAN_QUANTITY_CALLBACK(self)
            else:
                quantity = 1
        cu = self.stripe_customer

        subscription_params = {}
        if trial_days:
            subscription_params["trial_end"] = \
                datetime.datetime.utcnow() + datetime.timedelta(days=trial_days)
        if token:
            subscription_params["card"] = token

        subscription_params["plan"] = PAYMENTS_PLANS[plan]["stripe_plan_id"]
        subscription_params["quantity"] = quantity
        subscription_params["coupon"] = coupon
        resp = cu.update_subscription(**subscription_params)

        if token:
            # Refetch the stripe customer so we have the updated card info
            cu = self.stripe_customer
            self.save_card(cu)

        self.sync_current_subscription(cu)
        if charge_immediately:
            self.send_invoice()
        subscription_made.send(sender=self, plan=plan, stripe_response=resp)
        return resp

    def charge(self, amount, currency="usd", description=None,
               send_receipt=True, capture=True):
        """
        This method expects `amount` to be a Decimal type representing a
        dollar amount. It will be converted to cents so any decimals beyond
        two will be ignored.
        """
        if not isinstance(amount, decimal.Decimal):
            raise ValueError(
                "You must supply a decimal value representing dollars."
            )
        resp = stripe.Charge.create(
            amount=convert_amount_for_api(amount, currency),  # find the final amount
            currency=currency,
            customer=self.stripe_id,
            description=description,
            captured=capture,
        )
        obj = self.record_charge(resp["id"])
        if send_receipt:
            obj.send_receipt()
        return obj

    def record_charge(self, charge_id):
        data = stripe.Charge.retrieve(charge_id)
        return Charge.sync_from_stripe_data(data)


class CurrentSubscription(models.Model):

    customer = models.OneToOneField(
        Customer,
        related_name="current_subscription",
        null=True
    )
    plan = models.CharField(max_length=100)
    quantity = models.IntegerField()
    start = models.DateTimeField()
    # trialing, active, past_due, canceled, or unpaid
    status = models.CharField(max_length=25)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    trial_end = models.DateTimeField(blank=True, null=True)
    trial_start = models.DateTimeField(blank=True, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def total_amount(self):
        return self.amount * self.quantity

    def plan_display(self):
        return PAYMENTS_PLANS[self.plan]["name"]

    def status_display(self):
        return self.status.replace("_", " ").title()

    def is_period_current(self):
        return self.current_period_end > timezone.now()

    def is_status_current(self):
        return self.status in ["trialing", "active"]

    def is_valid(self):
        if not self.is_status_current():
            return False

        if self.cancel_at_period_end and not self.is_period_current():
            return False

        return True

    def delete(self, using=None):  # pylint: disable=E1002
        """
        Set values to None while deleting the object so that any lingering
        references will not show previous values (such as when an Event
        signal is triggered after a subscription has been deleted)
        """
        super(CurrentSubscription, self).delete(using=using)
        self.plan = None
        self.status = None
        self.quantity = 0
        self.amount = 0


class Invoice(models.Model):

    stripe_id = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, related_name="invoices")
    attempted = models.NullBooleanField()
    attempts = models.PositiveIntegerField(null=True)
    closed = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    period_end = models.DateTimeField()
    period_start = models.DateTimeField()
    subtotal = models.DecimalField(decimal_places=2, max_digits=9)
    total = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    date = models.DateTimeField()
    charge = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:  # pylint: disable=E0012,C1001
        ordering = ["-date"]

    def retry(self):
        if not self.paid and not self.closed:
            inv = stripe.Invoice.retrieve(self.stripe_id)
            inv.pay()
            return True
        return False

    def status(self):
        if self.paid:
            return "Paid"
        return "Open"

    @classmethod
    def sync_from_stripe_data(cls, stripe_invoice, send_receipt=True):
        c = Customer.objects.get(stripe_id=stripe_invoice["customer"])
        period_end = convert_tstamp(stripe_invoice, "period_end")
        period_start = convert_tstamp(stripe_invoice, "period_start")
        date = convert_tstamp(stripe_invoice, "date")

        invoice, created = cls.objects.get_or_create(
            stripe_id=stripe_invoice["id"],
            defaults=dict(
                customer=c,
                attempted=stripe_invoice["attempted"],
                attempts=stripe_invoice["attempt_count"],
                closed=stripe_invoice["closed"],
                paid=stripe_invoice["paid"],
                period_end=period_end,
                period_start=period_start,
                subtotal=convert_amount_for_db(stripe_invoice["subtotal"], stripe_invoice["currency"]),
                total=convert_amount_for_db(stripe_invoice["total"], stripe_invoice["currency"]),
                currency=stripe_invoice["currency"],
                date=date,
                charge=stripe_invoice.get("charge") or ""
            )
        )
        if not created:
            # pylint: disable=C0301
            invoice.attempted = stripe_invoice["attempted"]
            invoice.attempts = stripe_invoice["attempt_count"]
            invoice.closed = stripe_invoice["closed"]
            invoice.paid = stripe_invoice["paid"]
            invoice.period_end = period_end
            invoice.period_start = period_start
            invoice.subtotal = convert_amount_for_db(stripe_invoice["subtotal"], stripe_invoice["currency"])
            invoice.total = convert_amount_for_db(stripe_invoice["total"], stripe_invoice["currency"])
            invoice.currency = stripe_invoice["currency"]
            invoice.date = date
            invoice.charge = stripe_invoice.get("charge") or ""
            invoice.save()

        for item in stripe_invoice["lines"].get("data", []):
            period_end = convert_tstamp(item["period"], "end")
            period_start = convert_tstamp(item["period"], "start")

            if item.get("plan"):
                plan = plan_from_stripe_id(item["plan"]["id"])
            else:
                plan = ""

            inv_item, inv_item_created = invoice.items.get_or_create(
                stripe_id=item["id"],
                defaults=dict(
                    amount=convert_amount_for_db(item["amount"], item["currency"]),
                    currency=item["currency"],
                    proration=item["proration"],
                    description=item.get("description") or "",
                    line_type=item["type"],
                    plan=plan,
                    period_start=period_start,
                    period_end=period_end,
                    quantity=item.get("quantity")
                )
            )
            if not inv_item_created:
                inv_item.amount = convert_amount_for_db(item["amount"], item["currency"])
                inv_item.currency = item["currency"]
                inv_item.proration = item["proration"]
                inv_item.description = item.get("description") or ""
                inv_item.line_type = item["type"]
                inv_item.plan = plan
                inv_item.period_start = period_start
                inv_item.period_end = period_end
                inv_item.quantity = item.get("quantity")
                inv_item.save()

        if stripe_invoice.get("charge"):
            obj = c.record_charge(stripe_invoice["charge"])
            obj.invoice = invoice
            obj.save()
            if send_receipt:
                obj.send_receipt()
        return invoice

    @classmethod
    def handle_event(cls, event, send_receipt=SEND_EMAIL_RECEIPTS):
        valid_events = ["invoice.payment_failed", "invoice.payment_succeeded"]
        if event.kind in valid_events:
            invoice_data = event.message["data"]["object"]
            stripe_invoice = stripe.Invoice.retrieve(invoice_data["id"])
            cls.sync_from_stripe_data(stripe_invoice, send_receipt=send_receipt)


class InvoiceItem(models.Model):

    stripe_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    invoice = models.ForeignKey(Invoice, related_name="items")
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    proration = models.BooleanField(default=False)
    line_type = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    plan = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField(null=True)

    def plan_display(self):
        return PAYMENTS_PLANS[self.plan]["name"]


class Charge(StripeObject):

    customer = models.ForeignKey(Customer, related_name="charges")
    invoice = models.ForeignKey(Invoice, null=True, related_name="charges")
    card_last_4 = models.CharField(max_length=4, blank=True)
    card_kind = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, default="usd")
    amount = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    amount_refunded = models.DecimalField(
        decimal_places=2,
        max_digits=9,
        null=True
    )
    description = models.TextField(blank=True)
    paid = models.NullBooleanField(null=True)
    disputed = models.NullBooleanField(null=True)
    refunded = models.NullBooleanField(null=True)
    captured = models.NullBooleanField(null=True)
    fee = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    receipt_sent = models.BooleanField(default=False)
    charge_created = models.DateTimeField(null=True, blank=True)

    objects = ChargeManager()

    def calculate_refund_amount(self, amount=None):
        eligible_to_refund = self.amount - (self.amount_refunded or 0)
        if amount:
            return min(eligible_to_refund, amount)
        return eligible_to_refund

    def refund(self, amount=None):
        # pylint: disable=E1121
        charge_obj = stripe.Charge.retrieve(
            self.stripe_id
        ).refund(
            amount=convert_amount_for_api(self.calculate_refund_amount(amount=amount), self.currency)
        )
        Charge.sync_from_stripe_data(charge_obj)

    def capture(self, amount=None):
        self.captured = True
        charge_obj = stripe.Charge.retrieve(
            self.stripe_id
        ).capture(
            amount=convert_amount_for_api(self.calculate_refund_amount(amount=amount), self.currency)
        )
        Charge.sync_from_stripe_data(charge_obj)

    @classmethod
    def sync_from_stripe_data(cls, data):
        customer = Customer.objects.get(stripe_id=data["customer"])
        obj, _ = customer.charges.get_or_create(
            stripe_id=data["id"]
        )
        invoice_id = data.get("invoice", None)
        if obj.customer.invoices.filter(stripe_id=invoice_id).exists():
            obj.invoice = obj.customer.invoices.get(stripe_id=invoice_id)
        obj.card_last_4 = data["card"]["last4"]
        obj.card_kind = data["card"]["type"]
        obj.currency = data["currency"]
        obj.amount = convert_amount_for_db(data["amount"], obj.currency)
        obj.paid = data["paid"]
        obj.refunded = data["refunded"]
        obj.captured = data["captured"]
        obj.fee = convert_amount_for_db(data["fee"])  # assume in usd only
        obj.disputed = data["dispute"] is not None
        obj.charge_created = convert_tstamp(data, "created")
        if data.get("description"):
            obj.description = data["description"]
        if data.get("amount_refunded"):
            # pylint: disable=C0301
            obj.amount_refunded = convert_amount_for_db(data["amount_refunded"], obj.currency)
        if data["refunded"]:
            obj.amount_refunded = obj.amount
        obj.save()
        return obj

    def send_receipt(self):
        if not self.receipt_sent:
            site = Site.objects.get_current()
            protocol = getattr(settings, "DEFAULT_HTTP_PROTOCOL", "http")
            ctx = {
                "charge": self,
                "site": site,
                "protocol": protocol,
            }
            subject = render_to_string("payments/email/subject.txt", ctx)
            subject = subject.strip()
            message = render_to_string("payments/email/body.txt", ctx)
            num_sent = EmailMessage(
                subject,
                message,
                to=[self.customer.user.email],
                from_email=INVOICE_FROM_EMAIL
            ).send()
            self.receipt_sent = num_sent > 0
            self.save()
