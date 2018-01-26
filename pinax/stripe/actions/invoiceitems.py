import stripe
from django.utils.encoding import smart_str

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

def retrieve(invoiceitem_id):
    """
        Retrieve an invoiceitem object from Stripe's API

        Stripe throws an exception if the invoiceitem was not found, we are failing this exception
        silently and raising any other exception so the developer can know what went wrong.

        Args:
            invoiceitem_id: the Stripe ID of the invoiceitem you are fetching

        Returns:
            the data for a order object from the Stripe API
        """
    if not invoiceitem_id:
        return

    try:
        return stripe.InvoiceItem.retrieve(invoiceitem_id)
    except stripe.InvalidRequestError as e:
        if smart_str(e).find("No such invoiceitem") == -1:
            raise
        else:
            # Not Found
            return None

def delete(invoiceitem):
    """
    delete an invoiceitem

    Args:
        invoiceitem: the invoiceitem to delete
    """
    invoiceitem = retrieve(invoiceitem.id)
    if invoiceitem:
        invoiceitem.delete()