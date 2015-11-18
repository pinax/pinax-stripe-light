import datetime
import decimal
import json
import traceback

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from django.utils.encoding import smart_str

import stripe

from .. import hooks
from .. import managers
from .. import models
from .. import signals
from .. import utils


# Exceptions

class EventProcessingExceptionProxy(models.EventProcessingException):

    @classmethod
    def log(cls, data, exception, event=None):
        cls.objects.create(
            event=event,
            data=data or "",
            message=str(exception),
            traceback=traceback.format_exc() if isinstance(exception, Exception) else ""
        )


# Events

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
            "charge.dispute.closed",
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
                InvoiceProxy.handle_event(self)
            elif self.kind.startswith("charge."):
                self.customer.record_charge(
                    self.message["data"]["object"]["id"]
                )
            elif self.kind.startswith("transfer."):
                TransferProxy.process_transfer(
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

    @classmethod
    def dupe_exists(cls, stripe_id):
        return cls.objects.filter(stripe_id=stripe_id).exists()

    @classmethod
    def add_event(cls, stripe_id, kind, livemode, message):
        event = cls.objects.create(
            stripe_id=stripe_id,
            kind=kind,
            livemode=livemode,
            webhook_message=message
        )
        event.validate()
        event.process()


# Transfers

class TransferProxy(models.Transfer):

    class Meta:
        proxy = True

    @classmethod
    def during(cls, year, month):
        return cls.objects.filter(
            date__year=year,
            date__month=month
        )

    @classmethod
    def paid_totals_for(cls, year, month):
        return cls.during(year, month).filter(
            status="paid"
        ).aggregate(
            total_gross=Sum("charge_gross"),
            total_net=Sum("net"),
            total_charge_fees=Sum("charge_fees"),
            total_adjustment_fees=Sum("adjustment_fees"),
            total_refund_gross=Sum("refund_gross"),
            total_refund_fees=Sum("refund_fees"),
            total_validation_fees=Sum("validation_fees"),
            total_amount=Sum("amount")
        )

    def update_status(self):
        self.status = stripe.Transfer.retrieve(self.stripe_id).status
        self.save()

    @classmethod
    def process_transfer(cls, event, transfer):
        defaults = {
            "amount": utils.convert_amount_for_db(transfer["amount"], transfer["currency"]),
            "currency": transfer["currency"],
            "status": transfer["status"],
            "date": utils.convert_tstamp(transfer, "date"),
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
                "net": utils.convert_amount_for_db(summary.get("net"), transfer["currency"]),
            })
        for field in defaults:
            if field.endswith("fees") or field.endswith("gross"):
                defaults[field] = utils.convert_amount_for_db(defaults[field])  # assume in usd only
        if event.kind == "transfer.paid":
            defaults.update({"event": event})
            obj, created = cls.objects.get_or_create(
                stripe_id=transfer["id"],
                defaults=defaults
            )
        else:
            obj, created = cls.objects.get_or_create(
                stripe_id=transfer["id"],
                event=event,
                defaults=defaults
            )
        if created and summary:
            for fee in summary.get("charge_fee_details", []):
                obj.charge_fee_details.create(
                    amount=utils.convert_amount_for_db(fee["amount"], fee["currency"]),
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


# Invoices

class InvoiceProxy(models.Invoice):

    class Meta:
        proxy = True
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
        c = CustomerProxy.objects.get(stripe_id=stripe_invoice["customer"])
        period_end = utils.convert_tstamp(stripe_invoice, "period_end")
        period_start = utils.convert_tstamp(stripe_invoice, "period_start")
        date = utils.convert_tstamp(stripe_invoice, "date")

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
                subtotal=utils.convert_amount_for_db(stripe_invoice["subtotal"], stripe_invoice["currency"]),
                total=utils.convert_amount_for_db(stripe_invoice["total"], stripe_invoice["currency"]),
                currency=stripe_invoice["currency"],
                date=date,
                charge=stripe_invoice.get("charge") or ""
            )
        )
        if not created:
            invoice.attempted = stripe_invoice["attempted"]
            invoice.attempts = stripe_invoice["attempt_count"]
            invoice.closed = stripe_invoice["closed"]
            invoice.paid = stripe_invoice["paid"]
            invoice.period_end = period_end
            invoice.period_start = period_start
            invoice.subtotal = utils.convert_amount_for_db(stripe_invoice["subtotal"], stripe_invoice["currency"])
            invoice.total = utils.convert_amount_for_db(stripe_invoice["total"], stripe_invoice["currency"])
            invoice.currency = stripe_invoice["currency"]
            invoice.date = date
            invoice.charge = stripe_invoice.get("charge") or ""
            invoice.save()

        for item in stripe_invoice["lines"].get("data", []):
            period_end = utils.convert_tstamp(item["period"], "end")
            period_start = utils.convert_tstamp(item["period"], "start")

            if item.get("plan"):
                plan = utils.plan_from_stripe_id(item["plan"]["id"])
            else:
                plan = ""

            inv_item, inv_item_created = invoice.items.get_or_create(
                stripe_id=item["id"],
                defaults=dict(
                    amount=utils.convert_amount_for_db(item["amount"], item["currency"]),
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
                inv_item.amount = utils.convert_amount_for_db(item["amount"], item["currency"])
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
    def handle_event(cls, event, send_receipt=settings.PINAX_STRIPE_SEND_EMAIL_RECEIPTS):
        valid_events = ["invoice.payment_failed", "invoice.payment_succeeded"]
        if event.kind in valid_events:
            invoice_data = event.message["data"]["object"]
            stripe_invoice = stripe.Invoice.retrieve(invoice_data["id"])
            cls.sync_from_stripe_data(stripe_invoice, send_receipt=send_receipt)


# Customers

class CustomerProxy(models.Customer):

    objects = managers.CustomerManager()

    class Meta:
        proxy = True

    @property
    def stripe_customer(self):
        return stripe.Customer.retrieve(self.stripe_id)

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.get(user=user)

    def current_subscription(self):
        return next(iter(CurrentSubscriptionProxy.objects.filter(customer=self)), None)

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
        sub = self.current_subscription()
        return sub.is_valid() if sub is not None else False

    def cancel(self, at_period_end=True):
        try:
            current = self.current_subscription()
        except CurrentSubscriptionProxy.DoesNotExist:
            return
        sub = self.stripe_customer.cancel_subscription(
            at_period_end=at_period_end
        )
        current.status = sub.status
        current.cancel_at_period_end = sub.cancel_at_period_end
        current.current_period_end = utils.convert_tstamp(sub, "current_period_end")
        current.save()
        signals.cancelled.send(sender=self, stripe_response=sub)

    @classmethod
    def create(cls, user, card=None, plan=None, charge_immediately=True):

        if card and plan:
            plan = settings.PINAX_STRIPE_PLANS[plan]["stripe_plan_id"]
        elif settings.PINAX_STRIPE_DEFAULT_PLAN:
            plan = settings.PINAX_STRIPE_PLANS[settings.PINAX_STRIPE_DEFAULT_PLAN]["stripe_plan_id"]
        else:
            plan = None

        trial_end = hooks.hookset.trial_period(user, plan)

        stripe_customer = stripe.Customer.create(
            email=user.email,
            card=card,
            plan=plan or settings.PINAX_STRIPE_DEFAULT_PLAN,
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
        signals.card_changed.send(sender=self, stripe_response=cu)

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
            signals.card_changed.send(sender=self, stripe_response=cu)

    def sync_invoices(self, cu=None):
        cu = cu or self.stripe_customer
        for invoice in cu.invoices().data:
            InvoiceProxy.sync_from_stripe_data(invoice, send_receipt=False)

    def sync_charges(self, cu=None):
        cu = cu or self.stripe_customer
        for charge in cu.charges().data:
            self.record_charge(charge.id)

    def sync_current_subscription(self, cu=None):
        cu = cu or self.stripe_customer
        sub = getattr(cu, "subscription", None)
        if sub is None:
            try:
                self.current_subscription().delete()
            except CurrentSubscriptionProxy.DoesNotExist:
                pass
        else:
            sub_obj = self.current_subscription()
            if sub_obj is not None:
                sub_obj.plan = utils.plan_from_stripe_id(sub.plan.id)
                sub_obj.current_period_start = utils.convert_tstamp(
                    sub.current_period_start
                )
                sub_obj.current_period_end = utils.convert_tstamp(
                    sub.current_period_end
                )
                sub_obj.amount = utils.convert_amount_for_db(sub.plan.amount, sub.plan.currency)
                sub_obj.currency = sub.plan.currency
                sub_obj.status = sub.status
                sub_obj.cancel_at_period_end = sub.cancel_at_period_end
                sub_obj.start = utils.convert_tstamp(sub.start)
                sub_obj.quantity = sub.quantity
                sub_obj.save()
            else:
                sub_obj = CurrentSubscriptionProxy.objects.create(
                    customer=self,
                    plan=utils.plan_from_stripe_id(sub.plan.id),
                    current_period_start=utils.convert_tstamp(
                        sub.current_period_start
                    ),
                    current_period_end=utils.convert_tstamp(
                        sub.current_period_end
                    ),
                    amount=utils.convert_amount_for_db(sub.plan.amount, sub.plan.currency),
                    currency=sub.plan.currency,
                    status=sub.status,
                    cancel_at_period_end=sub.cancel_at_period_end,
                    start=utils.convert_tstamp(sub.start),
                    quantity=sub.quantity
                )

            if sub.trial_start and sub.trial_end:
                sub_obj.trial_start = utils.convert_tstamp(sub.trial_start)
                sub_obj.trial_end = utils.convert_tstamp(sub.trial_end)
                sub_obj.save()

            return sub_obj

    def update_plan_quantity(self, quantity, charge_immediately=False):
        self.subscribe(
            plan=utils.plan_from_stripe_id(
                self.stripe_customer.subscription.plan.id
            ),
            quantity=quantity,
            charge_immediately=charge_immediately
        )

    def subscribe(self, plan, quantity=None, trial_days=None, charge_immediately=True, token=None, coupon=None):
        quantity = hooks.hookset.adjust_subscription_quantity(customer=self, plan=plan, quantity=quantity)
        cu = self.stripe_customer

        subscription_params = {}
        if trial_days:
            subscription_params["trial_end"] = datetime.datetime.utcnow() + datetime.timedelta(days=trial_days)
        if token:
            subscription_params["card"] = token

        subscription_params["plan"] = settings.PINAX_STRIPE_PLANS[plan]["stripe_plan_id"]
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
        signals.subscription_made.send(sender=self, plan=plan, stripe_response=resp)
        return resp

    def charge(self, amount, currency="usd", description=None, send_receipt=True, capture=True):
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
            amount=utils.convert_amount_for_api(amount, currency),  # find the final amount
            currency=currency,
            customer=self.stripe_id,
            description=description,
            capture=capture,
        )
        obj = self.record_charge(resp["id"])
        if send_receipt:
            obj.send_receipt()
        return obj

    def record_charge(self, charge_id):
        data = stripe.Charge.retrieve(charge_id)
        return ChargeProxy.sync_from_stripe_data(data)


# Subscriptions

class CurrentSubscriptionProxy(models.CurrentSubscription):

    class Meta:
        proxy = True

    @property
    def total_amount(self):
        return self.amount * self.quantity

    def plan_display(self):
        return settings.PINAX_STRIPE_PLANS[self.plan]["name"]

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

    def delete(self, using=None):
        """
        Set values to None while deleting the object so that any lingering
        references will not show previous values (such as when an Event
        signal is triggered after a subscription has been deleted)
        """
        super(CurrentSubscriptionProxy, self).delete(using=using)
        self.plan = None
        self.status = None
        self.quantity = 0
        self.amount = 0


# Charges

class ChargeProxy(models.Charge):

    objects = managers.ChargeManager()

    class Meta:
        proxy = True

    def calculate_refund_amount(self, amount=None):
        eligible_to_refund = self.amount - (self.amount_refunded or 0)
        if amount:
            return min(eligible_to_refund, amount)
        return eligible_to_refund

    def refund(self, amount=None):
        charge_obj = stripe.Charge.retrieve(
            self.stripe_id
        ).refund(
            amount=utils.convert_amount_for_api(self.calculate_refund_amount(amount=amount), self.currency)
        )
        ChargeProxy.sync_from_stripe_data(charge_obj)

    def capture(self, amount=None):
        self.captured = True
        charge_obj = stripe.Charge.retrieve(
            self.stripe_id
        ).capture(
            amount=utils.convert_amount_for_api(self.calculate_refund_amount(amount=amount), self.currency)
        )
        ChargeProxy.sync_from_stripe_data(charge_obj)

    @classmethod
    def sync_from_stripe_data(cls, data):
        customer = CustomerProxy.objects.get(stripe_id=data["customer"])
        obj, _ = cls.objects.get_or_create(
            customer=customer,
            stripe_id=data["id"]
        )
        invoice_id = data.get("invoice", None)
        if obj.customer.invoices.filter(stripe_id=invoice_id).exists():
            obj.invoice = obj.customer.invoices.get(stripe_id=invoice_id)
        obj.card_last_4 = data["card"]["last4"]
        obj.card_kind = data["card"]["type"]
        obj.currency = data["currency"]
        obj.amount = utils.convert_amount_for_db(data["amount"], obj.currency)
        obj.paid = data["paid"]
        obj.refunded = data["refunded"]
        obj.captured = data["captured"]
        obj.fee = utils.convert_amount_for_db(data["fee"])  # assume in usd only
        obj.disputed = data["dispute"] is not None
        obj.charge_created = utils.convert_tstamp(data, "created")
        if data.get("description"):
            obj.description = data["description"]
        if data.get("amount_refunded"):
            obj.amount_refunded = utils.convert_amount_for_db(data["amount_refunded"], obj.currency)
        if data["refunded"]:
            obj.amount_refunded = obj.amount
        obj.save()
        return obj

    def send_receipt(self):
        hooks.hookset.send_receipt(self)
