import decimal

from django.db import models


class CustomerManager(models.Manager):

    def started_during(self, year, month):
        return self.exclude(
            subscription__status="trialing"
        ).filter(
            subscription__start__year=year,
            subscription__start__month=month
        )

    def active(self):
        return self.filter(
            subscription__status="active"
        )

    def canceled(self):
        return self.filter(
            subscription__status="canceled"
        )

    def canceled_during(self, year, month):
        return self.canceled().filter(
            subscription__canceled_at__year=year,
            subscription__canceled_at__month=month,
        )

    def started_plan_summary_for(self, year, month):
        return self.started_during(year, month).values(
            "subscription__plan"
        ).order_by().annotate(
            count=models.Count("subscription__plan")
        )

    def active_plan_summary(self):
        return self.active().values(
            "subscription__plan"
        ).order_by().annotate(
            count=models.Count("subscription__plan")
        )

    def canceled_plan_summary_for(self, year, month):
        return self.canceled_during(year, month).values(
            "subscription__plan"
        ).order_by().annotate(
            count=models.Count("subscription__plan")
        )

    def churn(self):
        canceled = self.canceled().count()
        active = self.active().count()
        return decimal.Decimal(str(canceled)) / decimal.Decimal(str(active))


class ChargeManager(models.Manager):

    def during(self, year, month):
        return self.filter(
            charge_created__year=year,
            charge_created__month=month
        )

    def paid_totals_for(self, year, month):
        return self.during(year, month).filter(
            paid=True
        ).aggregate(
            total_amount=models.Sum("amount"),
            total_refunded=models.Sum("amount_refunded")
        )
