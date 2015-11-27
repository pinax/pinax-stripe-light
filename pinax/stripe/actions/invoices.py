import stripe

from . import charges
from . import subscriptions
from ..conf import settings
from .. import proxies
from .. import utils


def create(customer):
    return stripe.Invoice.create(customer=customer.stripe_id)


def pay(invoice, send_receipt=True):
    if not invoice.paid and not invoice.closed:
        stripe_invoice = invoice.stripe_invoice.pay()
        sync_invoice_from_stripe_data(stripe_invoice, send_receipt=send_receipt)
        return True
    return False


def create_and_pay(customer):
    invoice = create(customer)
    try:
        if invoice.amount_due > 0:
            invoice.pay()
        return True
    except stripe.InvalidRequestError:
        return False  # There was nothing to Invoice


def sync_invoices_for_customer(customer):
    for invoice in customer.stripe_customer.invoices().data:
        sync_invoice_from_stripe_data(invoice, send_receipt=False)


def sync_invoice_items(invoice_proxy, items):
    """
    This assumes line items from a Stripe invoice.lines property and not through
    the invoicesitems resource calls. At least according to the documentation
    the data for an invoice item is slightly different between the two calls.

    For example, going through the invoiceitems resource you don't get a "type"
    field on the object.
    """
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
                stripe_subscription = subscriptions.retrieve(
                    invoice_proxy.customer,
                    item["id"]
                )
                item_subscription = subscriptions.sync_subscription_from_stripe_data(
                    invoice_proxy.customer,
                    stripe_subscription
                ) if stripe_subscription else None
            plan = item_subscription.plan if item_subscription is not None and plan is None else None
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
        utils.update_with_defaults(inv_item, defaults, inv_item_created)


def sync_invoice_from_stripe_data(stripe_invoice, send_receipt=settings.PINAX_STRIPE_SEND_EMAIL_RECEIPTS):
    c = proxies.CustomerProxy.objects.get(stripe_id=stripe_invoice["customer"])
    period_end = utils.convert_tstamp(stripe_invoice, "period_end")
    period_start = utils.convert_tstamp(stripe_invoice, "period_start")
    date = utils.convert_tstamp(stripe_invoice, "date")
    sub_id = stripe_invoice.get("subscription")

    if stripe_invoice.get("charge"):
        charge = charges.sync_charge_from_stripe_data(stripe.Charge.retrieve(stripe_invoice["charge"]))
        if send_receipt:
            charge.send_receipt()
    else:
        charge = None

    stripe_subscription = subscriptions.retrieve(c, sub_id)
    subscription = subscriptions.sync_subscription_from_stripe_data(c, stripe_subscription) if stripe_subscription else None

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

    invoice = utils.update_with_defaults(invoice, defaults, created)
    sync_invoice_items(invoice, stripe_invoice["lines"].get("data", []))

    return invoice
