from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from jsonfield.fields import JSONField

from .conf import settings


class StripeObject(models.Model):

    stripe_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class EventProcessingException(models.Model):

    event = models.ForeignKey("Event", null=True)
    data = models.TextField()
    message = models.CharField(max_length=500)
    traceback = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "<{}, pk={}, Event={}>".format(self.message, self.pk, self.event)


@python_2_unicode_compatible
class Event(StripeObject):

    kind = models.CharField(max_length=250)
    livemode = models.BooleanField(default=False)
    customer = models.ForeignKey("Customer", null=True)
    webhook_message = JSONField()
    validated_message = JSONField(null=True)
    valid = models.NullBooleanField(null=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return "%s - %s".format(self.kind, self.stripe_id)


class Transfer(StripeObject):
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


class TransferChargeFee(models.Model):

    transfer = models.ForeignKey(Transfer, related_name="charge_fee_details")
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    application = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    kind = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)


@python_2_unicode_compatible
class Customer(StripeObject):

    user = models.OneToOneField(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        null=True
    )
    card_fingerprint = models.CharField(max_length=200, blank=True)
    card_last_4 = models.CharField(max_length=4, blank=True)
    card_kind = models.CharField(max_length=50, blank=True)
    date_purged = models.DateTimeField(null=True, editable=False)

    def __str__(self):
        return str(self.user)


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
        return settings.PINAX_STRIPE_PLANS[self.plan]["name"]


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
