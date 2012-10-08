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
from payments.signals import purchase_made, cancelled, card_changed
from payments.signals import webhook_processing_error


def convert_tstamp(response, field_name):
    try:
        if response[field_name]:
            return datetime.datetime.fromtimestamp(
                response[field_name],
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
            cus_id = self.message["data"]["object"]["customer"]
        
        if cus_id is not None:
            try:
                self.customer = Customer.objects.get(stripe_id=cus_id)
                self.save()
            except Customer.DoesNotExist:
                pass
    
    def validate(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
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
            "charge.succeeded",
            "charge.failed",
            "charge.refunded",
            "charge.updated",
            "charge.disputed",
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
                    self.customer.record_charge(self.message["data"]["object"])
                elif self.kind.startswith("transfer."):
                    Transfer.process_transfer(self, self.message["data"]["object"])
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
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.status = stripe.Transfer.retrieve(self.stripe_id).status
        self.save()
    
    @classmethod
    def process_transfer(cls, event, transfer_obj):
        print "processing...", transfer_obj["id"]
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


class TransferChargeFee(models.Model):
    transfer = models.ForeignKey(Transfer, related_name="charge_fee_details")
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    application = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    kind = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)


class Customer(StripeObject):
    
    user = models.OneToOneField(User, null=True)
    
    plan = models.CharField(max_length=100, blank=True)
    
    card_fingerprint = models.CharField(max_length=200, blank=True)
    card_last_4 = models.CharField(max_length=4, blank=True)
    card_kind = models.CharField(max_length=50, blank=True)
    
    date_purged = models.DateTimeField(null=True, editable=False)
    
    @property
    def stripe_customer(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        return stripe.Customer.retrieve(self.stripe_id)
    
    def purge(self):
        self.stripe_customer.delete()
        self.user = None
        self.card_fingerprint = ""
        self.card_last_4 = ""
        self.card_kind = ""
        self.date_purged = timezone.now()
        self.save()
    
    def delete(self, using=None):
        # Only way to delete a customer is to use SQL
        self.purge()
    
    def display_plan(self):
        if self.plan:
            return PAYMENTS_PLANS[self.plan]["name"]
        return ""
    
    def can_charge(self):
        return self.card_fingerprint and \
               self.current_subscription.status not in ("canceled", "unpaid")
    
    def has_active_subscription(self):
        if not self.current_subscription:
            return False
        return self.current_subscription.is_valid()
    
    @property
    def current_subscription(self):
        if not hasattr(self, "_current_subscription"):
            try:
                self._current_subscription = self.subscriptions.latest()
            except Subscription.DoesNotExist:
                return None
        return self._current_subscription
    
    def cancel(self):
        sub = self.stripe_customer.cancel_subscription()
        period_end = convert_tstamp(sub, "current_period_end")
        self.current_subscription.status = sub.status
        self.current_subscription.period_end = period_end
        self.current_subscription.save()
        cancelled.send(sender=self, stripe_response=sub)
    
    @classmethod
    def create(cls, user):
        stripe.api_key = settings.STRIPE_SECRET_KEY
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
    
    def purchase(self, plan, trial_days=None):
        cu = self.stripe_customer
        if settings.PAYMENTS_PLANS[plan].get("stripe_plan_id"):
            if trial_days:
                resp = cu.update_subscription(
                    plan=PAYMENTS_PLANS[plan]["stripe_plan_id"],
                    trial_end=timezone.now() + datetime.timedelta(days=trial_days)
                )
            else:
                resp = cu.update_subscription(
                    plan=PAYMENTS_PLANS[plan]["stripe_plan_id"]
                )
            sub_obj, created = self.subscriptions.get_or_create(
                plan=plan_from_stripe_id(resp["plan"]["id"]),
                period_start=convert_tstamp(resp, "current_period_start"),
                period_end=convert_tstamp(resp, "current_period_end"),
                defaults={
                    "amount": (resp["plan"]["amount"] / 100.0),
                    "status": resp["status"]
                }
            )
            if resp.get("trial_start") and resp.get("trial_end"):
                sub_obj.trial_period_start = convert_tstamp(resp, "trial_start")
                sub_obj.trial_period_end = convert_tstamp(resp, "trial_end")
                sub_obj.save()
            if not created:
                sub_obj.amount = (resp["plan"]["amount"] / 100.0)
                sub_obj.status = resp["status"]
                sub_obj.save()
        else:
            # It's just a single transaction
            resp = stripe.Charge.create(
                amount=PAYMENTS_PLANS[plan]["price"] * 100,
                currency="usd",
                customer=self.stripe_id,
                description=PAYMENTS_PLANS[plan]["name"]
            )
            obj = self.record_charge(resp)
            obj.description = resp["description"]
            obj.save()
            obj.send_receipt()
        self.plan = plan
        self.save()
        purchase_made.send(sender=self, plan=plan, stripe_response=resp)
    
    def record_charge(self, data):
        obj, created = self.charges.get_or_create(
            stripe_id=data["id"]
        )
        obj.card_last_4 = data["card"]["last4"]
        obj.card_kind = data["card"]["type"]
        obj.amount = (data["amount"] / 100.0)
        obj.paid = data["paid"]
        obj.refunded = data["refunded"]
        obj.fee = (data["fee"] / 100.0)
        obj.disputed = data["disputed"]
        if data.get("description"):
            obj.description = data["description"]
        if data.get("amount_refunded"):
            obj.amount_refunded = (data["amount_refunded"] / 100.0)
        if data["refunded"]:
            obj.amount_refunded = (data["amount"] / 100.0)
        obj.save()
        return obj


class Subscription(models.Model):
    
    plan = models.CharField(max_length=100)
    customer = models.ForeignKey(Customer, related_name="subscriptions")
    period_end = models.DateTimeField()
    period_start = models.DateTimeField()
    trial_period_end = models.DateTimeField(null=True)
    trial_period_start = models.DateTimeField(null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    # trialing, active, past_due, canceled, or unpaid
    status = models.CharField(max_length=25)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def plan_display(self):
        return PAYMENTS_PLANS[self.plan]["name"]
    
    def status_display(self):
        return self.status.replace("_", " ").title()
    
    def is_period_current(self):
        return self.period_end > timezone.now()
    
    def is_status_current(self):
        return self.status in ["trialing", "active", "canceled"]
    
    def is_valid(self):
        return self.is_period_current() and self.is_status_current()
    
    class Meta:
        ordering = ["-period_end"]
        get_latest_by = "created_at"


class Invoice(StripeObject):
    
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
    subscriptions = models.ManyToManyField(
        Subscription,
        related_name="invoices",
        null=True
    )
    
    class Meta:
        ordering = ["-date"]
    
    def status(self):
        if self.paid:
            return "Paid"
        return "Open"
    
    @classmethod
    def create_from_stripe_data(cls, stripe_invoice):
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
            for item in stripe_invoice["lines"].get("invoiceitems", []):
                invoice.items.get_or_create(
                    stripe_id=item["id"],
                    amount=(item["amount"] / 100.0),
                    date=convert_tstamp(item, "date"),
                    description=item["description"]
                )
            for sub in stripe_invoice["lines"].get("subscriptions", []):
                period_end = convert_tstamp(sub["period"], "end")
                period_start = convert_tstamp(sub["period"], "start")
                subscription, created = Subscription.objects.get_or_create(
                    plan=plan_from_stripe_id(sub["plan"]["id"]),
                    customer=c,
                    period_start=period_start,
                    period_end=period_end,
                    defaults={
                        "amount": (sub["amount"] / 100.0)
                    }
                )
                subscription.status = c.stripe_customer.subscription.status
                subscription.amount = (sub["amount"] / 100.0)
                subscription.save()
                
                # @@@ what happens if the same sub.pk gets added twice?
                invoice.subscriptions.add(subscription)
            
            if stripe_invoice.get("charge"):
                charge = stripe.Charge.retrieve(stripe_invoice["charge"])
                desc = stripe_invoice["lines"]["subscriptions"][0]["plan"]["name"]
                obj = c.record_charge(charge)
                obj.invoice = invoice
                obj.description = desc
                obj.save()
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
    description = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField()
    amount = models.DecimalField(decimal_places=2, max_digits=7)


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
