import stripe

from .. import models
from .. import utils


def during(year, month):
    return models.Transfer.objects.filter(
        date__year=year,
        date__month=month
    )


def sync_transfer(transfer, event=None):
    """
    Syncronizes a transfer from the Stripe API

    Args:
        transfer: data from Stripe API representing transfer
        event: the event associated with the transfer
    """
    defaults = {
        "amount": utils.convert_amount_for_db(transfer["amount"], transfer["currency"]),
        "currency": transfer["currency"],
        "status": transfer["status"],
        "date": utils.convert_tstamp(transfer, "date"),
        "description": transfer.get("description", ""),
        "event": event
    }
    obj, created = models.Transfer.objects.get_or_create(
        stripe_id=transfer["id"],
        defaults=defaults
    )
    if not created:
        obj.status = transfer["status"]
        obj.save()


def update_status(transfer):
    transfer.status = stripe.Transfer.retrieve(transfer.stripe_id).status
    transfer.save()
