import stripe

from . import syncs


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
