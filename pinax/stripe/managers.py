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


class TieredPricingManager(models.Manager):

    TIERS_MODE_VOLUME = "volume"
    TIERS_MODE_GRADUATED = "graduated"
    TIERS_MODES = (TIERS_MODE_VOLUME, TIERS_MODE_GRADUATED)

    def closed_tiers(self, plan):
        return self.filter(plan=plan, up_to__isnull=False).order_by("up_to")

    def open_tiers(self, plan):
        return self.filter(plan=plan, up_to__isnull=True)

    def all_tiers(self, plan):
        return list(self.closed_tiers(plan)) + list(self.open_tiers(plan))

    def calculate_final_cost(self, plan, quantity, mode):
        if mode not in self.TIERS_MODES:
            raise Exception("Received wrong type of mode ({})".format(mode))

        all_tiers = self.all_tiers(plan)

        if mode == self.TIERS_MODE_VOLUME:
            applicable_tiers = filter(lambda t: quantity <= t.up_to, all_tiers)
            tier = applicable_tiers[0] if applicable_tiers else all_tiers[-1]
            cost = tier.calculate_cost(quantity)
        elif mode == self.TIERS_MODE_GRADUATED:
            quantity_billed = 0
            cost = 0
            idx = 0
            while quantity > 0:
                tier = all_tiers[idx]
                quantity_to_bill = min(quantity, tier.up_to - quantity_billed) if tier.up_to else quantity
                cost += tier.calculate_cost(quantity_to_bill)
                quantity -= quantity_to_bill
                quantity_billed += quantity_to_bill
                idx += 1
        else:
            cost = 0

        return cost
