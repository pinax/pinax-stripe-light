from __future__ import unicode_literals

import decimal

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property

import stripe

from jsonfield.fields import JSONField

from .conf import settings
from .managers import ChargeManager, CustomerManager
from .utils import CURRENCY_SYMBOLS


class StripeObject(models.Model):

    stripe_id = models.CharField(max_length=191, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class AccountRelatedStripeObject(StripeObject):

    stripe_account = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class Plan(AccountRelatedStripeObject):
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=15)
    interval = models.CharField(max_length=15)
    interval_count = models.IntegerField()
    name = models.CharField(max_length=150)
    statement_descriptor = models.TextField(blank=True)
    trial_period_days = models.IntegerField(null=True)
    metadata = JSONField(null=True)

    def __str__(self):
        return "{} ({}{})".format(self.name, CURRENCY_SYMBOLS.get(self.currency, ""), self.amount)


@python_2_unicode_compatible
class Coupon(StripeObject):

    amount_off = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    currency = models.CharField(max_length=10, default="usd")
    duration = models.CharField(max_length=10, default="once")
    duration_in_months = models.PositiveIntegerField(null=True)
    livemode = models.BooleanField(default=False)
    max_redemptions = models.PositiveIntegerField(null=True)
    metadata = JSONField(null=True)
    percent_off = models.PositiveIntegerField(null=True)
    redeem_by = models.DateTimeField(null=True)
    times_redeemed = models.PositiveIntegerField(null=True)
    valid = models.BooleanField(default=False)

    def __str__(self):
        if self.amount_off is None:
            description = "{}% off".format(self.percent_off,)
        else:
            description = "{}{}".format(CURRENCY_SYMBOLS.get(self.currency, ""), self.amount_off)

        return "Coupon for {}, {}".format(description, self.duration)


@python_2_unicode_compatible
class EventProcessingException(models.Model):

    event = models.ForeignKey("Event", null=True, on_delete=models.CASCADE)
    data = models.TextField()
    message = models.CharField(max_length=500)
    traceback = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "<{}, pk={}, Event={}>".format(self.message, self.pk, self.event)


@python_2_unicode_compatible
class Event(AccountRelatedStripeObject):

    kind = models.CharField(max_length=250)
    livemode = models.BooleanField(default=False)
    customer = models.ForeignKey("Customer", null=True, on_delete=models.CASCADE)
    webhook_message = JSONField()
    validated_message = JSONField(null=True)
    valid = models.NullBooleanField(null=True)
    processed = models.BooleanField(default=False)
    request = models.CharField(max_length=100, blank=True)
    pending_webhooks = models.PositiveIntegerField(default=0)
    api_version = models.CharField(max_length=100, blank=True)

    @property
    def message(self):
        return self.validated_message

    def __str__(self):
        return "{} - {}".format(self.kind, self.stripe_id)


class Transfer(AccountRelatedStripeObject):

    amount = models.DecimalField(decimal_places=2, max_digits=9)
    amount_reversed = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    application_fee = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)
    currency = models.CharField(max_length=25, default="usd")
    date = models.DateTimeField()
    description = models.TextField(null=True, blank=True)
    destination = models.TextField(null=True, blank=True)
    destination_payment = models.TextField(null=True, blank=True)
    event = models.ForeignKey(
        Event, related_name="transfers",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    failure_code = models.TextField(null=True, blank=True)
    failure_message = models.TextField(null=True, blank=True)
    livemode = models.BooleanField(default=False)
    metadata = JSONField(null=True, blank=True)
    method = models.TextField(null=True, blank=True)
    reversed = models.BooleanField(default=False)
    source_transaction = models.TextField(null=True, blank=True)
    source_type = models.TextField(null=True, blank=True)
    statement_descriptor = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=25)
    transfer_group = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)

    @property
    def stripe_transfer(self):
        return stripe.Transfer.retrieve(
            self.stripe_id,
            stripe_account=self.stripe_account
        )


class TransferChargeFee(models.Model):

    transfer = models.ForeignKey(Transfer, related_name="charge_fee_details", on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    application = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    kind = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)


@python_2_unicode_compatible
class Customer(AccountRelatedStripeObject):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    account_balance = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    currency = models.CharField(max_length=10, default="usd", blank=True)
    delinquent = models.BooleanField(default=False)
    default_source = models.TextField(blank=True)
    date_purged = models.DateTimeField(null=True, editable=False)

    objects = CustomerManager()

    @cached_property
    def stripe_customer(self):
        return stripe.Customer.retrieve(
            self.stripe_id,
            stripe_account=self.stripe_account
        )

    def __str__(self):
        return str(self.user)


class Card(StripeObject):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.TextField(blank=True)
    address_line_1 = models.TextField(blank=True)
    address_line_1_check = models.CharField(max_length=15)
    address_line_2 = models.TextField(blank=True)
    address_city = models.TextField(blank=True)
    address_state = models.TextField(blank=True)
    address_country = models.TextField(blank=True)
    address_zip = models.TextField(blank=True)
    address_zip_check = models.CharField(max_length=15)
    brand = models.TextField(blank=True)
    country = models.CharField(max_length=2, blank=True)
    cvc_check = models.CharField(max_length=15, blank=True)
    dynamic_last4 = models.CharField(max_length=4, blank=True)
    tokenization_method = models.CharField(max_length=15, blank=True)
    exp_month = models.IntegerField()
    exp_year = models.IntegerField()
    funding = models.CharField(max_length=15)
    last4 = models.CharField(max_length=4, blank=True)
    fingerprint = models.TextField()


class BitcoinReceiver(StripeObject):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    amount_received = models.DecimalField(decimal_places=2, max_digits=9, default=decimal.Decimal("0"))
    bitcoin_amount = models.PositiveIntegerField()  # Satoshi (10^8 Satoshi in one bitcoin)
    bitcoin_amount_received = models.PositiveIntegerField(default=0)
    bitcoin_uri = models.TextField(blank=True)
    currency = models.CharField(max_length=10, default="usd")
    description = models.TextField(blank=True)
    email = models.TextField(blank=True)
    filled = models.BooleanField(default=False)
    inbound_address = models.TextField(blank=True)
    payment = models.TextField(blank=True)
    refund_address = models.TextField(blank=True)
    uncaptured_funds = models.BooleanField(default=False)
    used_for_payment = models.BooleanField(default=False)


class Subscription(StripeObject):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    application_fee_percent = models.DecimalField(decimal_places=2, max_digits=3, default=None, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    start = models.DateTimeField()
    status = models.CharField(max_length=25)  # trialing, active, past_due, canceled, or unpaid
    trial_end = models.DateTimeField(blank=True, null=True)
    trial_start = models.DateTimeField(blank=True, null=True)

    @property
    def stripe_subscription(self):
        return stripe.Customer.retrieve(self.customer.stripe_id).subscriptions.retrieve(self.stripe_id)

    @property
    def total_amount(self):
        return self.plan.amount * self.quantity

    def plan_display(self):
        return self.plan.name

    def status_display(self):
        return self.status.replace("_", " ").title()

    def delete(self, using=None):
        """
        Set values to None while deleting the object so that any lingering
        references will not show previous values (such as when an Event
        signal is triggered after a subscription has been deleted)
        """
        super(Subscription, self).delete(using=using)
        self.status = None
        self.quantity = 0
        self.amount = 0


class Invoice(StripeObject):

    customer = models.ForeignKey(Customer, related_name="invoices", on_delete=models.CASCADE)
    amount_due = models.DecimalField(decimal_places=2, max_digits=9)
    attempted = models.NullBooleanField()
    attempt_count = models.PositiveIntegerField(null=True)
    charge = models.ForeignKey("Charge", null=True, related_name="invoices", on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, null=True, on_delete=models.CASCADE)
    statement_descriptor = models.TextField(blank=True)
    currency = models.CharField(max_length=10, default="usd")
    closed = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    paid = models.BooleanField(default=False)
    receipt_number = models.TextField(blank=True)
    period_end = models.DateTimeField()
    period_start = models.DateTimeField()
    subtotal = models.DecimalField(decimal_places=2, max_digits=9)
    tax = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    tax_percent = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    total = models.DecimalField(decimal_places=2, max_digits=9)
    date = models.DateTimeField()
    webhooks_delivered_at = models.DateTimeField(null=True)

    @property
    def status(self):
        return "Paid" if self.paid else "Open"

    @property
    def stripe_invoice(self):
        return stripe.Invoice.retrieve(
            self.stripe_id,
            stripe_account=self.customer.stripe_account
        )


class InvoiceItem(models.Model):

    stripe_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    kind = models.CharField(max_length=25, blank=True)
    subscription = models.ForeignKey(Subscription, null=True, on_delete=models.CASCADE)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    proration = models.BooleanField(default=False)
    line_type = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    plan = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=True)

    def plan_display(self):
        return self.plan.name if self.plan else ""


class Charge(StripeObject):

    customer = models.ForeignKey(Customer, null=True, related_name="charges", on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, null=True, related_name="charges", on_delete=models.CASCADE)
    source = models.CharField(max_length=100)
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
    receipt_sent = models.BooleanField(default=False)
    charge_created = models.DateTimeField(null=True, blank=True)

    # these fields are extracted from the BalanceTransaction for the
    # charge and help us know when funds from a charge are added to
    # our Stripe account balance
    available = models.BooleanField(default=False)
    available_on = models.DateTimeField(null=True, blank=True)

    transfer_group = models.TextField(null=True, blank=True)
 
    objects = ChargeManager()

    @property
    def stripe_charge(self):
        return stripe.Charge.retrieve(
            self.stripe_id,
            stripe_account=self.customer.stripe_account,
            expand=['balance_transaction']
        )

    @property
    def card(self):
        return Card.objects.filter(stripe_id=self.source).first()


class Account(StripeObject):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    business_name = models.TextField(blank=True, null=True)
    business_url = models.TextField(blank=True, null=True)

    charges_enabled = models.BooleanField(default=False)
    country = models.CharField(max_length=2)
    debit_negative_balances = models.BooleanField(default=False)
    decline_charge_on_avs_failure = models.BooleanField(default=False)
    decline_charge_on_cvc_failure = models.BooleanField(default=False)
    default_currency = models.CharField(max_length=3)
    details_submitted = models.BooleanField(default=False)
    display_name = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)

    legal_entity_address_city = models.TextField(null=True, blank=True)
    legal_entity_address_country = models.TextField(null=True, blank=True)
    legal_entity_address_line1 = models.TextField(null=True, blank=True)
    legal_entity_address_line2 = models.TextField(null=True, blank=True)
    legal_entity_address_postal_code = models.TextField(null=True, blank=True)
    legal_entity_address_state = models.TextField(null=True, blank=True)
    legal_entity_dob = models.DateField(null=True)
    legal_entity_first_name = models.TextField(null=True, blank=True)
    legal_entity_gender = models.TextField(null=True, blank=True)
    legal_entity_last_name = models.TextField(null=True, blank=True)
    legal_entity_maiden_name = models.TextField(null=True, blank=True)
    legal_entity_personal_id_number_provided = models.BooleanField(default=False)
    legal_entity_phone_number = models.TextField(null=True, blank=True)
    legal_entity_ssn_last_4_provided = models.BooleanField(default=False)
    legal_entity_type = models.TextField(null=True, blank=True)
    legal_entity_verification_details = models.TextField(null=True, blank=True)
    legal_entity_verification_details_code = models.TextField(null=True, blank=True)
    legal_entity_verification_document = models.TextField(null=True, blank=True)
    legal_entity_verification_status = models.TextField(null=True, blank=True)

    managed = models.NullBooleanField(null=True)
    metadata = JSONField(null=True)

    product_description = models.TextField(null=True, blank=True)
    statement_descriptor = models.TextField(null=True, blank=True)
    support_email = models.TextField(null=True, blank=True)
    support_phone = models.TextField(null=True, blank=True)

    timezone = models.TextField(null=True, blank=True)

    tos_acceptance_date = models.DateField(null=True)
    tos_acceptance_ip = models.TextField(null=True, blank=True)
    tos_acceptance_user_agent = models.TextField(null=True, blank=True)

    transfer_schedule_delay_days = models.PositiveSmallIntegerField(null=True)
    transfer_schedule_interval = models.TextField(null=True, blank=True)

    transfer_schedule_monthly_anchor = models.PositiveSmallIntegerField(null=True)
    transfer_schedule_weekly_anchor = models.TextField(null=True, blank=True)

    transfer_statement_descriptor = models.TextField(null=True, blank=True)
    transfers_enabled = models.BooleanField(default=False)

    verification_disabled_reason = models.TextField(null=True, blank=True)
    verification_due_by = models.DateTimeField(null=True, blank=True)
    verification_timestamp = models.DateTimeField(null=True, blank=True)
    verification_fields_needed = JSONField(null=True)

    @property
    def stripe_account(self):
        return stripe.Account.retrieve(self.stripe_id)


class BankAccount(StripeObject):

    account = models.ForeignKey(Account, related_name='bank_accounts')
    account_holder_name = models.TextField()
    account_holder_type = models.TextField()
    bank_name = models.TextField()
    country = models.TextField()
    currency = models.TextField()
    default_for_currency = models.BooleanField(default=False)
    fingerprint = models.TextField()
    last4 = models.CharField(max_length=4)
    metadata = JSONField(null=True)
    routing_number = models.TextField()
    status = models.TextField()

    @property
    def stripe_bankaccount(self):
        return self.account.stripe_account.external_accounts.retrieve(
            self.stripe_id
        )
