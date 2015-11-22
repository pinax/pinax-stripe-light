from django.utils.encoding import smart_str

import stripe

from . import syncs
from .. import proxies


def create(customer):
    return stripe.Invoice.create(customer=customer.stripe_id)


def pay(invoice, send_receipt=True):
    if not invoice.paid and not invoice.closed:
        stripe_invoice = invoice.stripe_invoice.pay()
        syncs.sync_invoice_from_stripe_data(stripe_invoice, send_receipt=send_receipt)
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


def retry_unpaid(customer):
    syncs.sync_invoices_for_customer(customer)
    for inv in proxies.InvoiceProxy.objects.filter(customer=customer, paid=False, closed=False):
        try:
            inv.retry()  # Always retry unpaid invoices
        except stripe.InvalidRequestError as error:
            if smart_str(error) != "Invoice is already paid":
                raise error
