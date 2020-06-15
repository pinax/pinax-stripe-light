# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from six import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

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


class AccountRelatedStripeObjectMixin(models.Model):

    stripe_account = models.ForeignKey(
        "pinax_stripe.Account",
        on_delete=models.CASCADE,
        null=True,
        default=None,
        blank=True,
    )

    @property
    def stripe_account_stripe_id(self):
        return getattr(self.stripe_account, "stripe_id", None)
    stripe_account_stripe_id.fget.short_description = "Stripe Account"

    class Meta:
        abstract = True


class AccountRelatedStripeObject(AccountRelatedStripeObjectMixin, StripeObject):
    """Uses a mixin to support Django 1.8 (name clash for stripe_id)"""

    class Meta:
        abstract = True


class UniquePerAccountStripeObject(AccountRelatedStripeObjectMixin):
    stripe_id = models.CharField(max_length=191)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
        unique_together = ("stripe_id", "stripe_account")


class StripeAccountFromCustomerMixin(object):
    @property
    def stripe_account(self):
        customer = getattr(self, "customer", None)
        return customer.stripe_account if customer else None

    @property
    def stripe_account_stripe_id(self):
        return self.stripe_account.stripe_id if self.stripe_account else None
    stripe_account_stripe_id.fget.short_description = "Stripe Account"


@python_2_unicode_compatible
class Plan(UniquePerAccountStripeObject):
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=15, blank=False)
    interval = models.CharField(max_length=15)
    interval_count = models.IntegerField()
    name = models.CharField(max_length=150)
    statement_descriptor = models.TextField(blank=True)
    trial_period_days = models.IntegerField(null=True, blank=True)
    metadata = JSONField(null=True, blank=True)

    def __str__(self):
        return "{} ({}{})".format(self.name, CURRENCY_SYMBOLS.get(self.currency, ""), self.amount)

    def __repr__(self):
        return "Plan(pk={!r}, name={!r}, amount={!r}, currency={!r}, interval={!r}, interval_count={!r}, trial_period_days={!r}, stripe_id={!r})".format(
            self.pk,
            self.name,
            self.amount,
            self.currency,
            self.interval,
            self.interval_count,
            self.trial_period_days,
            self.stripe_id,
        )

    @property
    def stripe_plan(self):
        return stripe.Plan.retrieve(
            self.stripe_id,
            stripe_account=self.stripe_account_stripe_id,
        )


@python_2_unicode_compatible
class Coupon(StripeObject):

    amount_off = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    currency = models.CharField(max_length=10, default="usd")
    duration = models.CharField(max_length=10, default="once")
    duration_in_months = models.PositiveIntegerField(null=True, blank=True)
    livemode = models.BooleanField(default=False)
    max_redemptions = models.PositiveIntegerField(null=True, blank=True)
    metadata = JSONField(null=True, blank=True)
    percent_off = models.PositiveIntegerField(null=True, blank=True)
    redeem_by = models.DateTimeField(null=True, blank=True)
    times_redeemed = models.PositiveIntegerField(null=True, blank=True)
    valid = models.BooleanField(default=False)

    def __str__(self):
        if self.amount_off is None:
            description = "{}% off".format(self.percent_off,)
        else:
            description = "{}{}".format(CURRENCY_SYMBOLS.get(self.currency, ""), self.amount_off)

        return "Coupon for {}, {}".format(description, self.duration)


@python_2_unicode_compatible
class EventProcessingException(models.Model):

    event = models.ForeignKey("Event", null=True, blank=True, on_delete=models.CASCADE)
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
    customer = models.ForeignKey("Customer", null=True, blank=True, on_delete=models.CASCADE)
    webhook_message = JSONField()
    validated_message = JSONField(null=True, blank=True)
    valid = models.NullBooleanField(null=True, blank=True)
    processed = models.BooleanField(default=False)
    request = models.CharField(max_length=100, blank=True)
    pending_webhooks = models.PositiveIntegerField(default=0)
    api_version = models.CharField(max_length=100, blank=True)

    @property
    def message(self):
        return self.validated_message

    def __str__(self):
        return "{} - {}".format(self.kind, self.stripe_id)

    def __repr__(self):
        return "Event(pk={!r}, kind={!r}, customer={!r}, valid={!r}, created_at={!s}, stripe_id={!r})".format(
            self.pk,
            self.kind,
            self.customer,
            self.valid,
            self.created_at.replace(microsecond=0).isoformat(),
            self.stripe_id,
        )


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
            stripe_account=self.stripe_account_stripe_id,
        )


class TransferChargeFee(models.Model):

    transfer = models.ForeignKey(Transfer, related_name="charge_fee_details", on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    application = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    kind = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)


class UserAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="user_accounts",
                             related_query_name="user_account",
                             on_delete=models.CASCADE)
    account = models.ForeignKey("pinax_stripe.Account",
                                related_name="user_accounts",
                                related_query_name="user_account",
                                on_delete=models.CASCADE)
    customer = models.ForeignKey("pinax_stripe.Customer",
                                 related_name="user_accounts",
                                 related_query_name="user_account",
                                 on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "account")

    def clean(self):
        if not self.customer.stripe_account == self.account:
            raise ValidationError(_("customer.stripe_account must be account."))
        return super(UserAccount, self).clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(UserAccount, self).save(*args, **kwargs)

    def __repr__(self):
        return "UserAccount(pk={self.pk!r}, user={self.user!r}, account={self.account!r}, customer={self.customer!r})".format(self=self)


@python_2_unicode_compatible
class Customer(AccountRelatedStripeObject):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through=UserAccount,
                                   related_name="customers",
                                   related_query_name="customers")
    account_balance = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    currency = models.CharField(max_length=10, default="usd", blank=True)
    delinquent = models.BooleanField(default=False)
    default_source = models.TextField(blank=True)
    date_purged = models.DateTimeField(null=True, blank=True, editable=False)

    objects = CustomerManager()

    @cached_property
    def stripe_customer(self):
        return stripe.Customer.retrieve(
            self.stripe_id,
            stripe_account=self.stripe_account_stripe_id,
        )

    def __str__(self):
        if self.user:
            return str(self.user)
        elif self.id:
            users = self.users.all()
            if users:
                return ", ".join(str(user) for user in users)
        if self.stripe_id:
            return "No User(s) ({})".format(self.stripe_id)
        return "No User(s)"

    def __repr__(self):
        if self.user:
            return "Customer(pk={!r}, user={!r}, stripe_id={!r})".format(
                self.pk,
                self.user,
                self.stripe_id,
            )
        elif self.id:
            return "Customer(pk={!r}, users={}, stripe_id={!r})".format(
                self.pk,
                ", ".join(repr(user) for user in self.users.all()),
                self.stripe_id,
            )
        return "Customer(pk={!r}, stripe_id={!r})".format(self.pk, self.stripe_id)


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

    def __repr__(self):
        return "Card(pk={!r}, customer={!r})".format(
            self.pk,
            getattr(self, "customer", None),
        )


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


class Subscription(StripeAccountFromCustomerMixin, StripeObject):

    STATUS_CURRENT = ["trialing", "active"]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    application_fee_percent = models.DecimalField(decimal_places=2, max_digits=3, default=None, null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    start = models.DateTimeField()
    status = models.CharField(max_length=25)  # trialing, active, past_due, canceled, or unpaid
    trial_end = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)

    @property
    def stripe_subscription(self):
        return stripe.Subscription.retrieve(self.stripe_id, stripe_account=self.stripe_account_stripe_id)

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

    def __repr__(self):
        return "Subscription(pk={!r}, customer={!r}, plan={!r}, status={!r}, stripe_id={!r})".format(
            self.pk,
            getattr(self, "customer", None),
            getattr(self, "plan", None),
            self.status,
            self.stripe_id,
        )


class Invoice(StripeAccountFromCustomerMixin, StripeObject):

    customer = models.ForeignKey(Customer, related_name="invoices", on_delete=models.CASCADE)
    amount_due = models.DecimalField(decimal_places=2, max_digits=9)
    attempted = models.NullBooleanField()
    attempt_count = models.PositiveIntegerField(null=True, blank=True)
    charge = models.ForeignKey("Charge", null=True, blank=True, related_name="invoices", on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.CASCADE)
    statement_descriptor = models.TextField(blank=True)
    currency = models.CharField(max_length=10, default="usd")
    closed = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    paid = models.BooleanField(default=False)
    receipt_number = models.TextField(blank=True)
    period_end = models.DateTimeField()
    period_start = models.DateTimeField()
    subtotal = models.DecimalField(decimal_places=2, max_digits=9)
    tax = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    tax_percent = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    total = models.DecimalField(decimal_places=2, max_digits=9)
    date = models.DateTimeField()
    webhooks_delivered_at = models.DateTimeField(null=True, blank=True)

    @property
    def status(self):
        return "Paid" if self.paid else "Open"

    @property
    def stripe_invoice(self):
        return stripe.Invoice.retrieve(
            self.stripe_id,
            stripe_account=self.stripe_account_stripe_id,
        )


class InvoiceItem(models.Model):

    stripe_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=9)
    currency = models.CharField(max_length=10, default="usd")
    kind = models.CharField(max_length=25, blank=True)
    subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.CASCADE)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    proration = models.BooleanField(default=False)
    line_type = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    plan = models.ForeignKey(Plan, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=True, blank=True)

    def plan_display(self):
        return self.plan.name if self.plan else ""


class Charge(StripeAccountFromCustomerMixin, StripeObject):

    customer = models.ForeignKey(Customer, null=True, blank=True, related_name="charges", on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, null=True, blank=True, related_name="charges", on_delete=models.CASCADE)
    source = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=10, default="usd")
    amount = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    amount_refunded = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    description = models.TextField(blank=True)
    paid = models.NullBooleanField(null=True, blank=True)
    disputed = models.NullBooleanField(null=True, blank=True)
    refunded = models.NullBooleanField(null=True, blank=True)
    captured = models.NullBooleanField(null=True, blank=True)
    receipt_sent = models.BooleanField(default=False)
    charge_created = models.DateTimeField(null=True, blank=True)

    # These fields are extracted from the BalanceTransaction for the
    # charge and help us to know when funds from a charge are added to
    # our Stripe account's balance.
    available = models.BooleanField(default=False)
    available_on = models.DateTimeField(null=True, blank=True)
    fee = models.DecimalField(
        decimal_places=2, max_digits=9, null=True, blank=True
    )
    fee_currency = models.CharField(max_length=10, null=True, blank=True)

    transfer_group = models.TextField(null=True, blank=True)
    outcome = JSONField(null=True, blank=True)

    objects = ChargeManager()

    def __str__(self):
        info = []
        if not self.paid:
            info += ["unpaid"]
        if not self.captured:
            info += ["uncaptured"]
        if self.refunded:
            info += ["refunded"]
        currency = CURRENCY_SYMBOLS.get(self.currency, "")
        return "{}{}{}".format(
            currency,
            self.total_amount,
            " ({})".format(", ".join(info)) if info else "",
        )

    def __repr__(self):
        return "Charge(pk={!r}, customer={!r}, source={!r}, amount={!r}, captured={!r}, paid={!r}, stripe_id={!r})".format(
            self.pk,
            self.customer,
            self.source,
            self.amount,
            self.captured,
            self.paid,
            self.stripe_id,
        )

    @property
    def total_amount(self):
        amount = self.amount if self.amount else 0
        amount_refunded = self.amount_refunded if self.amount_refunded else 0
        return amount - amount_refunded
    total_amount.fget.short_description = "Σ amount"

    @property
    def stripe_charge(self):
        return stripe.Charge.retrieve(
            self.stripe_id,
            stripe_account=self.stripe_account_stripe_id,
            expand=["balance_transaction"]
        )

    @property
    def card(self):
        return Card.objects.filter(stripe_id=self.source).first()


@python_2_unicode_compatible
class Account(StripeObject):

    INTERVAL_CHOICES = (
        ("Manual", "manual"),
        ("Daily", "daily"),
        ("Weekly", "weekly"),
        ("Monthly", "monthly"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="stripe_accounts")

    business_name = models.TextField(null=True, blank=True)
    business_url = models.TextField(null=True, blank=True)

    charges_enabled = models.BooleanField(default=False)
    country = models.CharField(max_length=2)
    debit_negative_balances = models.BooleanField(default=False)
    decline_charge_on_avs_failure = models.BooleanField(default=False)
    decline_charge_on_cvc_failure = models.BooleanField(default=False)
    default_currency = models.CharField(max_length=3)
    details_submitted = models.BooleanField(default=False)
    display_name = models.TextField(blank=True, null=True)
    email = models.TextField(null=True, blank=True)

    legal_entity_address_city = models.TextField(null=True, blank=True)
    legal_entity_address_country = models.TextField(null=True, blank=True)
    legal_entity_address_line1 = models.TextField(null=True, blank=True)
    legal_entity_address_line2 = models.TextField(null=True, blank=True)
    legal_entity_address_postal_code = models.TextField(null=True, blank=True)
    legal_entity_address_state = models.TextField(null=True, blank=True)
    legal_entity_dob = models.DateField(null=True, blank=True)
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

    # The type of the Stripe account. Can be "standard", "express", or "custom".
    type = models.TextField(null=True, blank=True)

    metadata = JSONField(null=True, blank=True)

    stripe_publishable_key = models.CharField(null=True, blank=True, max_length=100)

    product_description = models.TextField(null=True, blank=True)
    statement_descriptor = models.TextField(null=True, blank=True)
    support_email = models.TextField(null=True, blank=True)
    support_phone = models.TextField(null=True, blank=True)

    timezone = models.TextField(null=True, blank=True)

    tos_acceptance_date = models.DateField(null=True, blank=True)
    tos_acceptance_ip = models.TextField(null=True, blank=True)
    tos_acceptance_user_agent = models.TextField(null=True, blank=True)

    payout_schedule_delay_days = models.PositiveSmallIntegerField(null=True, blank=True)
    payout_schedule_interval = models.CharField(max_length=7, choices=INTERVAL_CHOICES, null=True, blank=True)
    payout_schedule_monthly_anchor = models.PositiveSmallIntegerField(null=True, blank=True)
    payout_schedule_weekly_anchor = models.TextField(null=True, blank=True)
    payout_statement_descriptor = models.TextField(null=True, blank=True)
    payouts_enabled = models.BooleanField(default=False)

    verification_disabled_reason = models.TextField(null=True, blank=True)
    verification_due_by = models.DateTimeField(null=True, blank=True)
    verification_timestamp = models.DateTimeField(null=True, blank=True)
    verification_fields_needed = JSONField(null=True, blank=True)
    authorized = models.BooleanField(default=True)

    @property
    def stripe_account(self):
        return stripe.Account.retrieve(self.stripe_id)

    def __str__(self):
        return "{} - {}".format(self.display_name or "", self.stripe_id)

    def __repr__(self):
        return "Account(pk={!r}, display_name={!r}, type={!r}, authorized={!r}, stripe_id={!r})".format(
            self.pk,
            self.display_name or "",
            self.type,
            self.authorized,
            self.stripe_id,
        )


class BankAccount(StripeObject):

    account = models.ForeignKey(Account, related_name="bank_accounts", on_delete=models.CASCADE)
    account_holder_name = models.TextField()
    account_holder_type = models.TextField()
    bank_name = models.TextField(null=True, blank=True)
    country = models.TextField()
    currency = models.TextField()
    default_for_currency = models.BooleanField(default=False)
    fingerprint = models.TextField()
    last4 = models.CharField(max_length=4)
    metadata = JSONField(null=True, blank=True)
    routing_number = models.TextField()
    status = models.TextField()

    @property
    def stripe_bankaccount(self):
        return self.account.stripe_account.external_accounts.retrieve(
            self.stripe_id
        )
