import datetime
import decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from ..models import Charge, Customer, Plan, Subscription, Tier


class CustomerManagerTest(TestCase):

    def setUp(self):
        User = get_user_model()
        # create customers and current subscription records
        period_start = datetime.datetime(2013, 4, 1, tzinfo=timezone.utc)
        period_end = datetime.datetime(2013, 4, 30, tzinfo=timezone.utc)
        start = datetime.datetime(2013, 1, 1, tzinfo=timezone.utc)
        self.plan = Plan.objects.create(
            stripe_id="p1",
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        self.plan2 = Plan.objects.create(
            stripe_id="p2",
            amount=5,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Light"
        )
        for i in range(10):
            customer = Customer.objects.create(
                user=User.objects.create_user(username="patrick{0}".format(i)),
                stripe_id="cus_xxxxxxxxxxxxxx{0}".format(i)
            )
            Subscription.objects.create(
                stripe_id="sub_{}".format(i),
                customer=customer,
                plan=self.plan,
                current_period_start=period_start,
                current_period_end=period_end,
                status="active",
                start=start,
                quantity=1
            )
        customer = Customer.objects.create(
            user=User.objects.create_user(username="patrick{0}".format(11)),
            stripe_id="cus_xxxxxxxxxxxxxx{0}".format(11)
        )
        Subscription.objects.create(
            stripe_id="sub_{}".format(11),
            customer=customer,
            plan=self.plan,
            current_period_start=period_start,
            current_period_end=period_end,
            status="canceled",
            canceled_at=period_end,
            start=start,
            quantity=1
        )
        customer = Customer.objects.create(
            user=User.objects.create_user(username="patrick{0}".format(12)),
            stripe_id="cus_xxxxxxxxxxxxxx{0}".format(12)
        )
        Subscription.objects.create(
            stripe_id="sub_{}".format(12),
            customer=customer,
            plan=self.plan2,
            current_period_start=period_start,
            current_period_end=period_end,
            status="active",
            start=start,
            quantity=1
        )

    def test_started_during_no_records(self):
        self.assertEqual(
            Customer.objects.started_during(2013, 4).count(),
            0
        )

    def test_started_during_has_records(self):
        self.assertEqual(
            Customer.objects.started_during(2013, 1).count(),
            12
        )

    def test_canceled_during(self):
        self.assertEqual(
            Customer.objects.canceled_during(2013, 4).count(),
            1
        )

    def test_canceled_all(self):
        self.assertEqual(
            Customer.objects.canceled().count(),
            1
        )

    def test_active_all(self):
        self.assertEqual(
            Customer.objects.active().count(),
            11
        )

    def test_started_plan_summary(self):
        for plan in Customer.objects.started_plan_summary_for(2013, 1):
            if plan["subscription__plan"] == self.plan:
                self.assertEqual(plan["count"], 11)
            if plan["subscription__plan"] == self.plan2:
                self.assertEqual(plan["count"], 1)

    def test_active_plan_summary(self):
        for plan in Customer.objects.active_plan_summary():
            if plan["subscription__plan"] == self.plan:
                self.assertEqual(plan["count"], 10)
            if plan["subscription__plan"] == self.plan2:
                self.assertEqual(plan["count"], 1)

    def test_canceled_plan_summary(self):
        for plan in Customer.objects.canceled_plan_summary_for(2013, 1):
            if plan["subscription__plan"] == self.plan:
                self.assertEqual(plan["count"], 1)
            if plan["subscription__plan"] == self.plan2:
                self.assertEqual(plan["count"], 0)

    def test_churn(self):
        self.assertEqual(
            Customer.objects.churn(),
            decimal.Decimal("1") / decimal.Decimal("11")
        )


class ChargeManagerTests(TestCase):

    def setUp(self):
        customer = Customer.objects.create(
            user=get_user_model().objects.create_user(username="patrick"),
            stripe_id="cus_xxxxxxxxxxxxxx"
        )
        Charge.objects.create(
            stripe_id="ch_1",
            customer=customer,
            charge_created=datetime.datetime(2013, 1, 1, tzinfo=timezone.utc),
            paid=True,
            amount=decimal.Decimal("100"),
            amount_refunded=decimal.Decimal("0")
        )
        Charge.objects.create(
            stripe_id="ch_2",
            customer=customer,
            charge_created=datetime.datetime(2013, 1, 1, tzinfo=timezone.utc),
            paid=True,
            amount=decimal.Decimal("100"),
            amount_refunded=decimal.Decimal("10")
        )
        Charge.objects.create(
            stripe_id="ch_3",
            customer=customer,
            charge_created=datetime.datetime(2013, 1, 1, tzinfo=timezone.utc),
            paid=False,
            amount=decimal.Decimal("100"),
            amount_refunded=decimal.Decimal("0")
        )
        Charge.objects.create(
            stripe_id="ch_4",
            customer=customer,
            charge_created=datetime.datetime(2013, 4, 1, tzinfo=timezone.utc),
            paid=True,
            amount=decimal.Decimal("500"),
            amount_refunded=decimal.Decimal("15.42")
        )

    def test_charges_during(self):
        charges = Charge.objects.during(2013, 1)
        self.assertEqual(charges.count(), 3)

    def test_paid_totals_for_jan(self):
        totals = Charge.objects.paid_totals_for(2013, 1)
        self.assertEqual(totals["total_amount"], decimal.Decimal("200"))
        self.assertEqual(totals["total_refunded"], decimal.Decimal("10"))

    def test_paid_totals_for_apr(self):
        totals = Charge.objects.paid_totals_for(2013, 4)
        self.assertEqual(totals["total_amount"], decimal.Decimal("500"))
        self.assertEqual(totals["total_refunded"], decimal.Decimal("15.42"))

    def test_paid_totals_for_dec(self):
        totals = Charge.objects.paid_totals_for(2013, 12)
        self.assertEqual(totals["total_amount"], None)
        self.assertEqual(totals["total_refunded"], None)


class TieredPricingManagerTests(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            stripe_id="plan", amount=0, interval="monthly", interval_count=1, billing_scheme=Plan.BILLING_SCHEME_TIERED
        )
        Tier.objects.create(plan=self.plan, up_to=5, amount=5, flat_amount=10)
        Tier.objects.create(plan=self.plan, up_to=10, amount=4, flat_amount=20)
        Tier.objects.create(plan=self.plan, up_to=15, amount=3, flat_amount=30)
        Tier.objects.create(plan=self.plan, up_to=20, amount=2, flat_amount=40)
        Tier.objects.create(plan=self.plan, up_to=None, amount=1, flat_amount=50)

    def test_calculate_final_cost_with_volume_tiers_mode(self):
        test_cases = [
            (1, 5),
            (5, 25),
            (6, 24),
            (20, 40),
            (25, 25),
        ]
        self.plan.tiers.all().update(flat_amount=0)
        for quantity, expected in test_cases:
            cost = Tier.pricing.calculate_final_cost(self.plan, quantity, Tier.pricing.TIERS_MODE_VOLUME)
            self.assertEqual(cost, expected)

    def test_calculate_final_cost_with_graduated_tiers_mode(self):
        test_cases = [
            (1, 5),
            (5, 25),
            (6, 29),
            (20, 70),
            (25, 75),
        ]
        self.plan.tiers.all().update(flat_amount=0)
        for quantity, expected in test_cases:
            cost = Tier.pricing.calculate_final_cost(self.plan, quantity, Tier.pricing.TIERS_MODE_GRADUATED)
            self.assertEqual(cost, expected)

    def test_calculate_final_cost_with_volume_tiers_and_flat_fees(self):
        test_cases = [
            (12, 66)
        ]
        for quantity, expected in test_cases:
            cost = Tier.pricing.calculate_final_cost(self.plan, quantity, Tier.pricing.TIERS_MODE_VOLUME)
            self.assertEqual(cost, expected)

    def test_calculate_final_cost_with_graduated_tiers_and_flat_fees(self):
        test_cases = [
            (12, 111)
        ]
        for quantity, expected in test_cases:
            cost = Tier.pricing.calculate_final_cost(self.plan, quantity, Tier.pricing.TIERS_MODE_GRADUATED)
            self.assertEqual(cost, expected)

    def test_calculate_final_cost_with_invalid_tier(self):
        try:
            Tier.pricing.calculate_final_cost(self.plan, 1, "invalid")
            self.fail("Excepted an exception from calculate_total_amount")
        except:
            pass
