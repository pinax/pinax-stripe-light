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

    def update_status(self):
        self.status = stripe.Transfer.retrieve(self.stripe_id).status
        self.save()
