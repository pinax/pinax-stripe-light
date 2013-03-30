import datetime
import json
import traceback

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.utils import timezone
from django.template.loader import render_to_string

from django.contrib.auth.models import User
from django.contrib.sites.models import Site

import stripe

from jsonfield.fields import JSONField

from payments.settings import PAYMENTS_PLANS, INVOICE_FROM_EMAIL
from payments.settings import plan_from_stripe_id
from payments.signals import WEBHOOK_SIGNALS
from payments.signals import subscription_made, cancelled, card_changed
from payments.signals import webhook_processing_error


stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = getattr(settings, "STRIPE_API_VERSION", "2012-11-07")


def convert_tstamp(response, field_name=None):
    try:
        if field_name and response[field_name]:
            return datetime.datetime.fromtimestamp(
                response[field_name],
                timezone.utc
            )
        if not field_name:
            return datetime.datetime.fromtimestamp(
                response,
                timezone.utc
            )
    except KeyError:
        pass
    return None


class StripeObject(models.Model):
    
    stripe_id = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
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
        return u"<%s, pk=%s, Event=%s>" % (self.message, self.pk, self.event)


class Event(StripeObject):
    
    kind = models.CharField(max_length=250)
    livemode = models.BooleanField()
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
    
    def process(self):
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
        if self.valid and not self.processed:
            try:
                if not self.kind.startswith("plan.") and not self.kind.startswith("transfer."):
                    self.link_customer()
                if self.kind.startswith("invoice."):
                    Invoice.handle_event(self)
                elif self.kind.startswith("charge."):
                    if not self.customer:
                        self.link_customer()
                    self.customer.record_charge(self.message["data"]["object"]["id"])
                elif self.kind.startswith("transfer."):
                    Transfer.process_transfer(self, self.message["data"]["object"])
                elif self.kind.startswith("customer.subscription."):
                    if not self.customer:
                        self.link_customer()
                    self.customer.sync_current_subscription()
                self.send_signal()
                self.processed = True
                self.save()
            except stripe.StripeError, e:
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
    event = models.ForeignKey(Event, related_name="transfers")
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    status = models.CharField(max_length=25)
    date = models.DateTimeField()
    description = models.TextField(null=True, blank=True)
    adjustment_count = models.IntegerField()
    adjustment_fees = models.DecimalField(decimal_places=2, max_digits=7)
    adjustment_gross = models.DecimalField(decimal_places=2, max_digits=7)
    charge_count = models.IntegerField()
    charge_fees = models.DecimalField(decimal_places=2, max_digits=7)
    charge_gross = models.DecimalField(decimal_places=2, max_digits=7)
    collected_fee_count = models.IntegerField()
    collected_fee_gross = models.DecimalField(decimal_places=2, max_digits=7)
    net = models.DecimalField(decimal_places=2, max_digits=7)
    refund_count = models.IntegerField()
    refund_fees = models.DecimalField(decimal_places=2, max_digits=7)
    refund_gross = models.DecimalField(decimal_places=2, max_digits=7)
    validation_count = models.IntegerField()
    validation_fees = models.DecimalField(decimal_places=2, max_digits=7)
    
    def update_status(self):
        self.status = stripe.Transfer.retrieve(self.stripe_id).status
        self.save()
    
    @classmethod
    def process_transfer(cls, event, transfer_obj):
        obj, created = Transfer.objects.get_or_create(
            stripe_id=transfer_obj["id"],
            event=event,
            defaults={
                "amount": transfer_obj["amount"] / 100.0,
                "status": transfer_obj["status"],
                "date": convert_tstamp(transfer_obj, "date"),
                "description": transfer_obj.get("description", ""),
                "adjustment_count": transfer_obj["summary"]["adjustment_count"],
                "adjustment_fees": transfer_obj["summary"]["adjustment_fees"] / 100.0,
                "adjustment_gross": transfer_obj["summary"]["adjustment_gross"] / 100.0,
                "charge_count": transfer_obj["summary"]["charge_count"],
                "charge_fees": transfer_obj["summary"]["charge_fees"] / 100.0,
                "charge_gross": transfer_obj["summary"]["charge_gross"] / 100.0,
                "collected_fee_count": transfer_obj["summary"]["collected_fee_count"] / 100.0,
                "collected_fee_gross": transfer_obj["summary"]["collected_fee_gross"] / 100.0,
                "net": transfer_obj["summary"]["net"] / 100.0,
                "refund_count": transfer_obj["summary"]["refund_count"],
                "refund_fees": transfer_obj["summary"]["refund_fees"] / 100.0,
                "refund_gross": transfer_obj["summary"]["refund_gross"] / 100.0,
                "validation_count": transfer_obj["summary"]["validation_count"],
                "validation_fees": transfer_obj["summary"]["validation_fees"] / 100.0,
            }
        )
        if created:
            for fee in transfer_obj["summary"]["charge_fee_details"]:
                obj.charge_fee_details.create(
                    amount=fee["amount"] / 100.0,
                    application=fee.get("application", ""),
                    description=fee.get("description", ""),
                    kind=fee["type"]
                )
        else:
            obj.status = transfer_obj["status"]
            obj.save()
        if event.kind == "transfer.updated":
            obj.update_status()


class TransferChargeFee(models.Model):
    transfer = models.ForeignKey(Transfer, related_name="charge_fee_details")
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    application = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    kind = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)


class Customer(StripeObject):
    
    user = models.OneToOneField(User, null=True)
    card_fingerprint = models.CharField(max_length=200, blank=True)
    card_last_4 = models.CharField(max_length=4, blank=True)
    card_kind = models.CharField(max_length=50, blank=True)
    date_purged = models.DateTimeField(null=True, editable=False)
    
    def __unicode__(self):
        return unicode(self.user)
    
    @property
    def stripe_customer(self):
        return stripe.Customer.retrieve(self.stripe_id)
    
    def purge(self):
        try:
            self.stripe_customer.delete()
        except stripe.InvalidRequestError as e:
            if e.message.startswith("No such customer:"):
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
        try:
            return self.card_fingerprint and \
                   self.current_subscription.status not in ("canceled", "unpaid")
        except CurrentSubscription.DoesNotExist:
            return False
    
    def has_active_subscription(self):
        try:
            return self.current_subscription.is_valid()
        except CurrentSubscription.DoesNotExist:
            return False
    
    def cancel(self):
        try:
            current = self.current_subscription
        except CurrentSubscription.DoesNotExist:
            return
        sub = self.stripe_customer.cancel_subscription()
        current.status = sub.status
        current.period_end = convert_tstamp(sub, "current_period_end")
        current.save()
        cancelled.send(sender=self, stripe_response=sub)
    
    @classmethod
    def create(cls, user):
        customer = stripe.Customer.create(
            email=user.email
        )
        return Customer.objects.create(
            user=user,
            stripe_id=customer.id
        )
    
    def update_card(self, token):
        cu = self.stripe_customer
        cu.card = token
        cu.save()
        self.card_fingerprint = cu.active_card.fingerprint
        self.card_last_4 = cu.active_card.last4
        self.card_kind = cu.active_card.type
        self.save()
        card_changed.send(sender=self, stripe_response=cu)
    
    def send_invoice(self):
        try:
            invoice = stripe.Invoice.create(customer=self.stripe_id)
            invoice.pay()
            return True
        except stripe.InvalidRequestError:
            return False  # There was nothing to invoice
    
    def sync(self, cu=None):
        cu = cu or self.stripe_customer
        if cu.active_card:
            self.card_fingerprint = cu.active_card.fingerprint
            self.card_last_4 = cu.active_card.last4
            self.card_kind = cu.active_card.type
            self.save()
    
    def sync_invoices(self, cu=None):
        cu = cu or self.stripe_customer
        for invoice in cu.invoices().data:
            Invoice.create_from_stripe_data(invoice, send_receipt=False)
    
    def sync_charges(self, cu=None):
        cu = cu or self.stripe_customer
        for charge in cu.charges().data:
            self.record_charge(charge.id)
    
    def sync_current_subscription(self, cu=None):
        cu = cu or self.stripe_customer
        sub = cu.subscription
        if sub:
            try:
                sub_obj = self.current_subscription
                sub_obj.plan = plan_from_stripe_id(sub.plan.id)
                sub_obj.current_period_start = convert_tstamp(sub.current_period_start)
                sub_obj.current_period_end = convert_tstamp(sub.current_period_end)
                sub_obj.amount = (sub.plan.amount / 100.0)
                sub_obj.status = sub.status
                sub_obj.start = convert_tstamp(sub.start)
                sub_obj.quantity = sub.quantity
                sub_obj.save()
            except CurrentSubscription.DoesNotExist:
                sub_obj = CurrentSubscription.objects.create(
                    customer=self,
                    plan=plan_from_stripe_id(sub.plan.id),
                    current_period_start=convert_tstamp(sub.current_period_start),
                    current_period_end=convert_tstamp(sub.current_period_end),
                    amount=(sub.plan.amount / 100.0),
                    status=sub.status,
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
            plan=plan_from_stripe_id(self.stripe_customer.subscription.plan.id),
            quantity=quantity,
            charge_immediately=charge_immediately
        )
    
    def subscribe(self, plan, quantity=1, trial_days=None, charge_immediately=True):
        cu = self.stripe_customer
        if trial_days:
            resp = cu.update_subscription(
                plan=PAYMENTS_PLANS[plan]["stripe_plan_id"],
                trial_end=timezone.now() + datetime.timedelta(days=trial_days),
                quantity=quantity
            )
        else:
            resp = cu.update_subscription(
                plan=PAYMENTS_PLANS[plan]["stripe_plan_id"],
                quantity=quantity
            )
        self.sync_current_subscription()
        if charge_immediately:
            self.send_invoice()
        subscription_made.send(sender=self, plan=plan, stripe_response=resp)
    
    def charge(self, amount, currency="usd", description=None):
        resp = stripe.Charge.create(
            amount=amount,
            currency=currency,
            customer=self.stripe_id,
            description=description,
        )
        obj = self.record_charge(resp["id"])
        obj.send_receipt()
    
    def record_charge(self, charge_id):
        data = stripe.Charge.retrieve(charge_id)
        obj, created = self.charges.get_or_create(
            stripe_id=data["id"]
        )
        if data.get("invoice") and self.invoices.filter(stripe_id=data.get("invoice")).exists():
            obj.invoice = self.invoices.get(stripe_id=data.get("invoice"))
        obj.card_last_4 = data["card"]["last4"]
        obj.card_kind = data["card"]["type"]
        obj.amount = (data["amount"] / 100.0)
        obj.paid = data["paid"]
        obj.refunded = data["refunded"]
        obj.fee = (data["fee"] / 100.0)
        obj.disputed = data["dispute"] is not None
        if data.get("description"):
            obj.description = data["description"]
        if data.get("amount_refunded"):
            obj.amount_refunded = (data["amount_refunded"] / 100.0)
        if data["refunded"]:
            obj.amount_refunded = (data["amount"] / 100.0)
        obj.save()
        return obj


class CurrentSubscription(models.Model):
    
    customer = models.OneToOneField(Customer, related_name="current_subscription", null=True)
    plan = models.CharField(max_length=100)
    quantity = models.IntegerField()
    start = models.DateTimeField()
    status = models.CharField(max_length=25)  # trialing, active, past_due, canceled, or unpaid
    canceled_at = models.DateTimeField(null=True)
    current_period_end = models.DateTimeField(null=True)
    current_period_start = models.DateTimeField(null=True)
    ended_at = models.DateTimeField(null=True)
    trial_end = models.DateTimeField(null=True)
    trial_start = models.DateTimeField(null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def plan_display(self):
        return PAYMENTS_PLANS[self.plan]["name"]
    
    def status_display(self):
        return self.status.replace("_", " ").title()
    
    def is_period_current(self):
        return self.current_period_end > timezone.now()
    
    def is_status_current(self):
        return self.status in ["trialing", "active", "canceled"]
    
    def is_valid(self):
        return self.is_period_current() and self.is_status_current()


class Invoice(models.Model):
    
    stripe_id = models.CharField(max_length=50)
    customer = models.ForeignKey(Customer, related_name="invoices")
    attempted = models.NullBooleanField()
    attempts = models.PositiveIntegerField(null=True)
    closed = models.BooleanField()
    paid = models.BooleanField()
    period_end = models.DateTimeField()
    period_start = models.DateTimeField()
    subtotal = models.DecimalField(decimal_places=2, max_digits=7)
    total = models.DecimalField(decimal_places=2, max_digits=7)
    date = models.DateTimeField()
    charge = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ["-date"]
    
    def status(self):
        if self.paid:
            return "Paid"
        return "Open"
    
    @classmethod
    def create_from_stripe_data(cls, stripe_invoice, send_receipt=True):
        if not cls.objects.filter(stripe_id=stripe_invoice["id"]).exists():
            c = Customer.objects.get(stripe_id=stripe_invoice["customer"])
            
            period_end = convert_tstamp(stripe_invoice, "period_end")
            period_start = convert_tstamp(stripe_invoice, "period_start")
            date = convert_tstamp(stripe_invoice, "date")
            
            invoice = c.invoices.create(
                attempted=stripe_invoice["attempted"],
                closed=stripe_invoice["closed"],
                paid=stripe_invoice["paid"],
                period_end=period_end,
                period_start=period_start,
                subtotal=stripe_invoice["subtotal"] / 100.0,
                total=stripe_invoice["total"] / 100.0,
                date=date,
                charge=stripe_invoice.get("charge") or "",
                stripe_id=stripe_invoice["id"]
            )
            for item in stripe_invoice["lines"].get("data", []):
                period_end = convert_tstamp(item["period"], "end")
                period_start = convert_tstamp(item["period"], "start")
                
                if item.get("plan"):
                    plan = plan_from_stripe_id(item["plan"]["id"])
                else:
                    plan = ""
                invoice.items.create(
                    stripe_id=item["id"],
                    amount=(item["amount"] / 100.0),
                    currency=item["currency"],
                    proration=item["proration"],
                    description=item.get("description") or "",
                    line_type=item["type"],
                    plan=plan,
                    period_start=period_start,
                    period_end=period_end,
                    quantity=item.get("quantity")
                )
            
            if stripe_invoice.get("charge"):
                obj = c.record_charge(stripe_invoice["charge"])
                obj.invoice = invoice
                obj.save()
                if send_receipt:
                    obj.send_receipt()
            return invoice
    
    @classmethod
    def handle_event(cls, event):
        valid_events = ["invoice.payment_failed", "invoice.payment_succeeded"]
        if event.kind in valid_events:
            invoice_data = event.message["data"]["object"]
            stripe_invoice = stripe.Invoice.retrieve(invoice_data["id"])
            cls.create_from_stripe_data(stripe_invoice)


class InvoiceItem(StripeObject):
    
    invoice = models.ForeignKey(Invoice, related_name="items")
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    currency = models.CharField(max_length=10)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    proration = models.BooleanField()
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
    amount = models.DecimalField(decimal_places=2, max_digits=7, null=True)
    amount_refunded = models.DecimalField(
        decimal_places=2,
        max_digits=7,
        null=True
    )
    description = models.TextField(blank=True)
    paid = models.NullBooleanField(null=True)
    disputed = models.NullBooleanField(null=True)
    refunded = models.NullBooleanField(null=True)
    fee = models.DecimalField(decimal_places=2, max_digits=7, null=True)
    receipt_sent = models.BooleanField(default=False)
    
    def send_receipt(self):
        if not self.receipt_sent:
            site = Site.objects.get_current()
            subject = render_to_string(
                "payments/email/subject.txt",
                {"charge": self, "site": site}
            ).strip()
            message = render_to_string(
                "payments/email/body.txt",
                {"charge": self, "site": site}
            )
            num_sent = EmailMessage(
                subject,
                message,
                to=[self.customer.user.email],
                from_email=INVOICE_FROM_EMAIL
            ).send()
            self.receipt_sent = num_sent > 0
            self.save()
