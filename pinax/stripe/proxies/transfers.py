from django.db.models import Sum

import stripe

from .. import models
from .. import utils


class TransferProxy(models.Transfer):

    class Meta:
        proxy = True

    @classmethod
    def during(cls, year, month):
        return cls.objects.filter(
            date__year=year,
            date__month=month
        )

    @classmethod
    def paid_totals_for(cls, year, month):
        return cls.during(year, month).filter(
            status="paid"
        ).aggregate(
            total_gross=Sum("charge_gross"),
            total_net=Sum("net"),
            total_charge_fees=Sum("charge_fees"),
            total_adjustment_fees=Sum("adjustment_fees"),
            total_refund_gross=Sum("refund_gross"),
            total_refund_fees=Sum("refund_fees"),
            total_validation_fees=Sum("validation_fees"),
            total_amount=Sum("amount")
        )

    def update_status(self):
        self.status = stripe.Transfer.retrieve(self.stripe_id).status
        self.save()

    @classmethod
    def process_transfer(cls, event, transfer):
        defaults = {
            "amount": utils.convert_amount_for_db(transfer["amount"], transfer["currency"]),
            "currency": transfer["currency"],
            "status": transfer["status"],
            "date": utils.convert_tstamp(transfer, "date"),
            "description": transfer.get("description", "")
        }
        summary = transfer.get("summary")
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
                "net": utils.convert_amount_for_db(summary.get("net"), transfer["currency"]),
            })
        for field in defaults:
            if field.endswith("fees") or field.endswith("gross"):
                defaults[field] = utils.convert_amount_for_db(defaults[field])  # assume in usd only
        if event.kind == "transfer.paid":
            defaults.update({"event": event})
            obj, created = cls.objects.get_or_create(
                stripe_id=transfer["id"],
                defaults=defaults
            )
        else:
            obj, created = cls.objects.get_or_create(
                stripe_id=transfer["id"],
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
            obj.status = transfer["status"]
            obj.save()
        if event.kind == "transfer.updated":
            obj.update_status()
