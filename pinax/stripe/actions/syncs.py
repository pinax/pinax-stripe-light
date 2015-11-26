from django.utils.encoding import smart_str

import stripe

from ..conf import settings
from .. import utils
from .. import proxies


def sync_plans():
    for plan in stripe.Plan.all().data:
        defaults = dict(
            amount=utils.convert_amount_for_db(plan["amount"], plan["currency"]),
            currency=plan["currency"] or "",
            interval=plan["interval"],
            interval_count=plan["interval_count"],
            name=plan["name"],
            statement_descriptor=plan["statement_descriptor"] or "",
            trial_period_days=plan["trial_period_days"]
        )
        obj, created = proxies.PlanProxy.objects.get_or_create(
            stripe_id=plan["id"],
            defaults=defaults
        )
        if not created:
            for key in defaults:
                setattr(obj, key, defaults[key])
            obj.save()


def sync_payment_source_from_stripe_data(customer, source):
    if source["id"].startswith("card_"):
        defaults = dict(
            customer=customer,
            name=source["name"] or "",
            address_line_1=source["address_line1"] or "",
            address_line_1_check=source["address_line1_check"] or "",
            address_line_2=source["address_line2"] or "",
            address_city=source["address_city"] or "",
            address_state=source["address_state"] or "",
            address_country=source["address_country"] or "",
            address_zip=source["address_zip"] or "",
            address_zip_check=source["address_zip_check"] or "",
            brand=source["brand"],
            country=source["country"],
            cvc_check=source["cvc_check"],
            dynamic_last4=source["dynamic_last4"] or "",
            exp_month=source["exp_month"],
            exp_year=source["exp_year"],
            funding=source["funding"] or "",
            last4=source["last4"] or "",
            fingerprint=source["fingerprint"] or ""
        )
        card, created = proxies.CardProxy.objects.get_or_create(
            stripe_id=source["id"],
            defaults=defaults
        )
        if not created:
            for key in defaults:
                setattr(card, key, defaults[key])
            card.save()
    else:
        defaults = dict(
            customer=customer,
            active=source["active"],
            amount=utils.convert_amount_for_db(source["amount"], source["currency"]),
            amount_received=utils.convert_amount_for_db(source["amount_received"], source["currency"]),
            bitcoin_amount=source["bitcoin_amount"],
            bitcoin_amount_received=source["bitcoin_amount_received"],
            bitcoin_uri=source["bitcoin_uri"],
            currency=source["currency"],
            description=source["description"],
            email=source["email"],
            filled=source["filled"],
            inbound_address=source["inbound_address"],
            payment=source["payment"] if "payment" in source else "",
            refund_address=source["refund_address"] or "",
            uncaptured_funds=source["uncaptured_funds"],
            used_for_payment=source["used_for_payment"]
        )
        receiver, created = proxies.BitcoinRecieverProxy.objects.get_or_create(
            stripe_id=source["id"],
            defaults=defaults
        )
        if not created:
            for key in defaults:
                setattr(receiver, key, defaults[key])
            receiver.save()


def sync_subscription_from_stripe_data(customer, subscription):
    defaults = dict(
        customer=customer,
        application_fee_percent=subscription["application_fee_percent"],
        cancel_at_period_end=subscription["cancel_at_period_end"],
        canceled_at=utils.convert_tstamp(subscription["canceled_at"]),
        current_period_start=utils.convert_tstamp(subscription["current_period_start"]),
        current_period_end=utils.convert_tstamp(subscription["current_period_end"]),
        ended_at=utils.convert_tstamp(subscription["ended_at"]),
        plan=proxies.PlanProxy.objects.get(stripe_id=subscription["plan"]["id"]),
        quantity=subscription["quantity"],
        start=utils.convert_tstamp(subscription["start"]),
        status=subscription["status"],
        trial_start=utils.convert_tstamp(subscription["trial_start"]) if subscription["trial_start"] else None,
        trial_end=utils.convert_tstamp(subscription["trial_end"]) if subscription["trial_end"] else None
    )
    sub, created = proxies.SubscriptionProxy.objects.get_or_create(
        stripe_id=subscription["id"],
        defaults=defaults
    )
    if not created:
        for key in defaults:
            setattr(sub, key, defaults[key])
        sub.save()
    return sub


def sync_customer(customer, cu=None):
    if cu is None:
        cu = customer.stripe_customer
    customer.account_balance = utils.convert_amount_for_db(cu["account_balance"], cu["currency"])
    customer.currency = cu["currency"] or ""
    customer.delinquent = cu["delinquent"]
    customer.default_source = cu["default_source"] or ""
    customer.save()
    for source in cu["sources"]["data"]:
        sync_payment_source_from_stripe_data(customer, source)
    for subscription in cu["subscriptions"]["data"]:
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
    obj.source = data["source"]["id"]
    obj.currency = data["currency"]
    obj.invoice = next(iter(proxies.InvoiceProxy.objects.filter(stripe_id=data["invoice"])), None)
    obj.amount = utils.convert_amount_for_db(data["amount"], obj.currency)
    obj.paid = data["paid"]
    obj.refunded = data["refunded"]
    obj.captured = data["captured"]
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


def _sync_invoice_items(invoice_proxy, items):
    for item in items:
        period_end = utils.convert_tstamp(item["period"], "end")
        period_start = utils.convert_tstamp(item["period"], "start")

        if item.get("plan"):
            plan = proxies.PlanProxy.objects.get(stripe_id=item["plan"]["id"])
        else:
            plan = None

        if item["type"] == "subscription":
            if invoice_proxy.subscription and invoice_proxy.subscription.stripe_id == item["id"]:
                item_subscription = invoice_proxy.subscription
            else:
                stripe_subscription = _retrieve_stripe_subscription(
                    invoice_proxy.customer,
                    item["id"]
                )
                item_subscription = sync_subscription_from_stripe_data(
                    invoice_proxy.customer,
                    stripe_subscription
                ) if stripe_subscription else None
        else:
            item_subscription = None

        defaults = dict(
            amount=utils.convert_amount_for_db(item["amount"], item["currency"]),
            currency=item["currency"],
            proration=item["proration"],
            description=item.get("description") or "",
            line_type=item["type"],
            plan=plan,
            period_start=period_start,
            period_end=period_end,
            quantity=item.get("quantity"),
            subscription=item_subscription
        )
        inv_item, inv_item_created = invoice_proxy.items.get_or_create(
            stripe_id=item["id"],
            defaults=defaults
        )
        if not inv_item_created:
            for key in defaults:
                setattr(inv_item, key, defaults[key])
            inv_item.save()


def _retrieve_stripe_subscription(customer, sub_id):
    if sub_id:
        try:
            return customer.stripe_customer.subscriptions.retrieve(sub_id)
        except stripe.InvalidRequestError as e:
            if smart_str(e).find("does not have a subscription with ID") != -1:
                # The exception was thrown because the customer has deleted the
                # subscription we're attempting to sync, ignore the exception
                pass
            else:
                # The exception was raised for another reason, re-raise it
                raise


def sync_invoice_from_stripe_data(stripe_invoice, send_receipt=settings.PINAX_STRIPE_SEND_EMAIL_RECEIPTS):
    c = proxies.CustomerProxy.objects.get(stripe_id=stripe_invoice["customer"])
    period_end = utils.convert_tstamp(stripe_invoice, "period_end")
    period_start = utils.convert_tstamp(stripe_invoice, "period_start")
    date = utils.convert_tstamp(stripe_invoice, "date")
    sub_id = stripe_invoice.get("subscription")

    if stripe_invoice.get("charge"):
        charge = sync_charge_from_stripe_data(stripe.Charge.retrieve(stripe_invoice["charge"]))
        if send_receipt:
            charge.send_receipt()
    else:
        charge = None

    stripe_subscription = _retrieve_stripe_subscription(c, sub_id)
    subscription = sync_subscription_from_stripe_data(
        c, stripe_subscription) if stripe_subscription else None

    defaults = dict(
        customer=c,
        attempted=stripe_invoice["attempted"],
        attempt_count=stripe_invoice["attempt_count"],
        amount_due=utils.convert_amount_for_db(stripe_invoice["amount_due"], stripe_invoice["currency"]),
        closed=stripe_invoice["closed"],
        paid=stripe_invoice["paid"],
        period_end=period_end,
        period_start=period_start,
        subtotal=utils.convert_amount_for_db(stripe_invoice["subtotal"], stripe_invoice["currency"]),
        total=utils.convert_amount_for_db(stripe_invoice["total"], stripe_invoice["currency"]),
        currency=stripe_invoice["currency"],
        date=date,
        charge=charge,
        subscription=subscription
    )
    invoice, created = proxies.InvoiceProxy.objects.get_or_create(
        stripe_id=stripe_invoice["id"],
        defaults=defaults
    )
    if charge is not None:
        charge.invoice = invoice
        charge.save()
    if not created:
        for key in defaults:
            setattr(invoice, key, defaults[key])
        invoice.save()

    _sync_invoice_items(invoice, stripe_invoice["lines"].get("data", []))

    return invoice
