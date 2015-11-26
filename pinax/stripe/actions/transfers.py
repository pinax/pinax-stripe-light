from .. import proxies
from .. import utils


def process_transfer_event(event):
    stripe_transfer = event.message["data"]["object"]
    defaults = {
        "amount": utils.convert_amount_for_db(stripe_transfer["amount"], stripe_transfer["currency"]),
        "currency": stripe_transfer["currency"],
        "status": stripe_transfer["status"],
        "date": utils.convert_tstamp(stripe_transfer, "date"),
        "description": stripe_transfer.get("description", ""),
        "event": event
    }
    obj, created = proxies.TransferProxy.objects.get_or_create(
        stripe_id=stripe_transfer["id"],
        defaults=defaults
    )
    if not created:
        obj.status = stripe_transfer["status"]
        obj.save()
