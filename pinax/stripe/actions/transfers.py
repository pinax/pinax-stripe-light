from .. import proxies
from .. import utils


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
    obj, created = proxies.TransferProxy.objects.get_or_create(
        stripe_id=transfer["id"],
        defaults=defaults
    )
    if not created:
        obj.status = transfer["status"]
        obj.save()
