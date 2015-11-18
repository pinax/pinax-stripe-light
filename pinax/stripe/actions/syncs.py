import stripe

from .. import utils
from .. import signals
from .. import proxies


def sync_customer(customer):
    cu = customer.stripe_customer
    updated = False
    if hasattr(cu, "active_card") and cu.active_card:
        # Test to make sure the card has changed, otherwise do not update it
        # (i.e. refrain from sending any signals)
        if (customer.card_last_4 != cu.active_card.last4 or
                customer.card_fingerprint != cu.active_card.fingerprint or
                customer.card_kind != cu.active_card.type):
            updated = True
            customer.card_last_4 = cu.active_card.last4
            customer.card_fingerprint = cu.active_card.fingerprint
            customer.card_kind = cu.active_card.type
    else:
        updated = True
        customer.card_fingerprint = ""
        customer.card_last_4 = ""
        customer.card_kind = ""

    if updated:
        customer.save()
        signals.card_changed.send(sender=customer, stripe_response=cu)


def sync_invoices_for_customer(customer):
    for invoice in customer.stripe_customer.invoices().data:
        sync_invoice_from_stripe_data(invoice, send_receipt=False)


def sync_charges_for_customer(customer):
    for charge in customer.stripe_customer.charges().data:
        sync_charge_from_stripe_data(charge)


def sync_current_subscription_for_customer(customer):
    stripe_customer = customer.stripe_customer
    sub = getattr(stripe_customer, "subscription", None)
    sub_obj = customer.current_subscription()
    if sub is None:
        if sub_obj:
            sub_obj.delete()
    else:
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
            sub_obj = proxies.CurrentSubscriptionProxy.objects.create(
                customer=customer,
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


def sync_invoice_from_stripe_data(stripe_invoice, send_receipt=True):
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
