import stripe


def create(customer, amount, description, currency="usd", discountable=False, invoice=None, metadata=None, subscription=None):
    """
    Creates a Stripe invoice item

    Args:
        customer: the customer to create the invoice for (Customer)
        amount: The integer amount in cents of the charge to be applied to the upcoming invoice.
        description: An arbitrary string which you can attach to the invoice item.
        currency: Three-letter ISO currency code, in lowercase. Must be a supported currency.
        discountable: Controls whether discounts apply to this invoice item.
        invoice: The ID of an existing invoice to add this invoice item to. When left blank,
        the invoice item will be added to the next upcoming scheduled invoice.
        metadata: A set of key/value pairs that you can attach to an invoice item object.
        subscription: The ID of a subscription to add this invoice item to. When left blank,
        the invoice item will be be added to the next upcoming scheduled invoice.

    Returns:
        the data from the Stripe API that represents the invoice item object that
        was created
    """
    return stripe.InvoiceItem.create(
        amount=amount,
        customer=customer.stripe_id,
        description=description,
        currency=currency,
        discountable=discountable,
        invoice=invoice,
        metadata=metadata,
        subscription=subscription
    )