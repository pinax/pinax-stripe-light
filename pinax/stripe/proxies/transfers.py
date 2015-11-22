from django.db.models import Sum

import stripe

from .. import models


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
