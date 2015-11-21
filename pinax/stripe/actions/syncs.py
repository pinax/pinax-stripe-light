import stripe

from ..conf import settings
from .. import utils
from .. import proxies


def sync_payment_source_from_stripe_data(customer, source):
    if source.id.startswith("card_"):
        defaults = dict(
            customer=customer,
            name=source.name or "",
            address_line_1=source.address_line1 or "",
            address_line_1_check=source.address_line1_check or "",
            address_line_2=source.address_line2 or "",
            address_city=source.address_city or "",
            address_state=source.address_state or "",
            address_country=source.address_country or "",
            address_zip=source.address_zip or "",
            address_zip_check=source.address_zip_check or "",
            brand=source.brand,
            country=source.country,
            cvc_check=source.cvc_check,
            dynamic_last4=source.dynamic_last4 or "",
            exp_month=source.exp_month,
            exp_year=source.exp_year,
            funding=source.funding or "",
            last4=source.last4 or "",
            fingerprint=source.fingerprint or ""
        )
        card, created = proxies.CardProxy.objects.get_or_create(
            stripe_id=source.id,
            defaults=defaults
        )
        if not created:
            for key in defaults:
                setattr(card, key, defaults[key])
            card.save()
    else:
        defaults = dict(
            customer=customer,
            active=source.active,
            amount=utils.convert_amount_for_db(source.amount, source.currency),
            amount_received=utils.convert_amount_for_db(source.amount_received, source.currency),
            bitcoin_amount=source.bitcoin_amount,
            bitcoin_amount_received=source.bitcoin_amount_received,
            bitcoin_uri=source.bitcoin_uri,
            currency=source.currency,
            description=source.description,
            email=source.email,
            filled=source.filled,
            inbound_address=source.inbound_address,
            payment=source.payment,
            refund_address=source.refund_address,
            uncaptured_funds=source.uncaptured_funds,
            used_for_payment=source.used_for_payment
        )
        receiver, created = proxies.BitcoinRecieverProxy.objects.get_or_create(
            stripe_id=source.id,
            defaults=defaults
        )
        if not created:
            for key in defaults:
                setattr(receiver, key, defaults[key])
            receiver.save()


def sync_subscription_from_stripe_data(customer, subscription):
    defaults = dict(
        customer=customer,
        application_fee_percent=subscription.application_fee_percent,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=utils.convert_tstamp(subscription.canceled_at),
        current_period_start=utils.convert_tstamp(subscription.current_period_start),
        current_period_end=utils.convert_tstamp(subscription.current_period_end),
        ended_at=utils.convert_tstamp(subscription.ended_at),
        plan=utils.plan_from_stripe_id(subscription.plan.id),
        quantity=subscription.quantity,
        start=utils.convert_tstamp(subscription.start),
        status=subscription.status,
        trial_start=utils.convert_tstamp(subscription.trial_start) if subscription.trial_start else None,
        trial_end=utils.convert_tstamp(subscription.trial_end) if subscription.trial_end else None
    )
    sub, created = proxies.SubscriptionProxy.objects.get_or_create(
        stripe_id=subscription.id,
        defaults=defaults
    )
    if not created:
        for key in defaults:
            setattr(sub, key, defaults[key])
        sub.save()


def sync_customer(customer, cu=None):
    if cu is None:
        cu = customer.stripe_customer
    customer.account_balance = utils.convert_amount_for_db(cu.account_balance, cu.currency)
    customer.currency = cu.currency or ""
    customer.delinquent = cu.delinquent
    customer.default_source = cu.default_source or ""
    customer.save()
    for source in cu.sources.data:
        sync_payment_source_from_stripe_data(customer, source)
    for subscription in cu.subscriptions.data:
        sync_subscription_from_stripe_data(customer, subscription)


def sync_invoices_for_customer(customer):
    for invoice in customer.stripe_customer.invoices().data:
        sync_invoice_from_stripe_data(invoice, send_receipt=False)


def sync_charges_for_customer(customer):
    for charge in customer.stripe_customer.charges().data:
        sync_charge_from_stripe_data(charge)


def sync_charge_from_stripe_data(data):
    customer = proxies.CustomerProxy.objects.get(stripe_id=data["customer"])
    obj, _ = proxies.ChargeProxy.objects.get_or_create(
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


def fetch_and_sync_invoice(stripe_id, send_receipt=settings.PINAX_STRIPE_SEND_EMAIL_RECEIPTS):
    sync_invoice_from_stripe_data(stripe.Invoice.retrieve(stripe_id))


def sync_invoice_from_stripe_data(stripe_invoice, send_receipt=settings.PINAX_STRIPE_SEND_EMAIL_RECEIPTS):
    c = proxies.CustomerProxy.objects.get(stripe_id=stripe_invoice["customer"])
    period_end = utils.convert_tstamp(stripe_invoice, "period_end")
    period_start = utils.convert_tstamp(stripe_invoice, "period_start")
    date = utils.convert_tstamp(stripe_invoice, "date")

    invoice, created = proxies.InvoiceProxy.objects.get_or_create(
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
        obj = sync_charge_from_stripe_data(stripe.Charge.retrieve(stripe_invoice["charge"]))
        obj.invoice = invoice
        obj.save()
        if send_receipt:
            obj.send_receipt()
    return invoice
