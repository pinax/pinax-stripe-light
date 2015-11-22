from .. import proxies
from .. import utils


def process_transfer_event(event):
    stripe_transfer = event.message["data"]["object"]
    defaults = {
        "amount": utils.convert_amount_for_db(stripe_transfer["amount"], stripe_transfer["currency"]),
        "currency": stripe_transfer["currency"],
        "status": stripe_transfer["status"],
        "date": utils.convert_tstamp(stripe_transfer, "date"),
        "description": stripe_transfer.get("description", "")
    }
    summary = stripe_transfer.get("summary")
    if summary:
        defaults.update({
            "adjustment_count": summary.get("adjustment_count"),
            "adjustment_fees": summary.get("adjustment_fees"),
            "adjustment_gross": summary.get("adjustment_gross"),
            "charge_count": summary.get("charge_count"),
            "charge_fees": summary.get("charge_fees"),
            "charge_gross": summary.get("charge_gross"),
            "collected_fee_count": summary.get("collected_fee_count"),
            "collected_fee_gross": summary.get("collected_fee_gross"),
            "refund_count": summary.get("refund_count"),
            "refund_fees": summary.get("refund_fees"),
            "refund_gross": summary.get("refund_gross"),
            "validation_count": summary.get("validation_count"),
            "validation_fees": summary.get("validation_fees"),
            "net": utils.convert_amount_for_db(summary.get("net"), stripe_transfer["currency"]),
        })
    for field in defaults:
        if field.endswith("fees") or field.endswith("gross"):
            defaults[field] = utils.convert_amount_for_db(defaults[field])  # assume in usd only
    if event.kind == "transfer.paid":
        defaults.update({"event": event})
        obj, created = proxies.TransferProxy.objects.get_or_create(
            stripe_id=stripe_transfer["id"],
            defaults=defaults
        )
    else:
        obj, created = proxies.TransferProxy.objects.get_or_create(
            stripe_id=stripe_transfer["id"],
            event=event,
            defaults=defaults
        )
    if created and summary:
        for fee in summary.get("charge_fee_details", []):
            obj.charge_fee_details.create(
                amount=utils.convert_amount_for_db(fee["amount"], fee["currency"]),
                currency=fee["currency"],
                application=fee.get("application", ""),
                description=fee.get("description", ""),
                kind=fee["type"]
            )
    else:
        obj.status = stripe_transfer["status"]
        obj.save()
    if event.kind == "transfer.updated":
        obj.update_status()
