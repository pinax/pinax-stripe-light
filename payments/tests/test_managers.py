import datetime
import decimal

from django.test import TestCase
from django.utils import timezone

from . import TRANSFER_CREATED_TEST_DATA, TRANSFER_CREATED_TEST_DATA2
from ..models import Event, Transfer, Customer, CurrentSubscription, Charge
from ..utils import get_user_model


class CustomerManagerTest(TestCase):

    def setUp(self):
        User = get_user_model()
        # create customers and current subscription records
        period_start = datetime.datetime(2013, 4, 1, tzinfo=timezone.utc)
        period_end = datetime.datetime(2013, 4, 30, tzinfo=timezone.utc)
        start = datetime.datetime(2013, 1, 1, tzinfo=timezone.utc)
        for i in range(10):
            customer = Customer.objects.create(
                user=User.objects.create_user(username="patrick{0}".format(i)),
                stripe_id="cus_xxxxxxxxxxxxxx{0}".format(i),
                card_fingerprint="YYYYYYYY",
                card_last_4="2342",
                card_kind="Visa"
            )
            CurrentSubscription.objects.create(
                customer=customer,
                plan="test",
                current_period_start=period_start,
                current_period_end=period_end,
                amount=(500 / decimal.Decimal("100.0")),
                status="active",
                start=start,
                quantity=1
            )
        customer = Customer.objects.create(
            user=User.objects.create_user(username="patrick{0}".format(11)),
            stripe_id="cus_xxxxxxxxxxxxxx{0}".format(11),
            card_fingerprint="YYYYYYYY",
            card_last_4="2342",
            card_kind="Visa"
        )
        CurrentSubscription.objects.create(
            customer=customer,
            plan="test",
            current_period_start=period_start,
            current_period_end=period_end,
            amount=(500 / decimal.Decimal("100.0")),
            status="canceled",
            canceled_at=period_end,
            start=start,
            quantity=1
        )
        customer = Customer.objects.create(
            user=User.objects.create_user(username="patrick{0}".format(12)),
            stripe_id="cus_xxxxxxxxxxxxxx{0}".format(12),
            card_fingerprint="YYYYYYYY",
            card_last_4="2342",
            card_kind="Visa"
        )
        CurrentSubscription.objects.create(
            customer=customer,
            plan="test-2",
            current_period_start=period_start,
            current_period_end=period_end,
            amount=(500 / decimal.Decimal("100.0")),
            status="active",
            start=start,
            quantity=1
        )

    def test_started_during_no_records(self):
        self.assertEquals(
            Customer.objects.started_during(2013, 4).count(),
            0
        )

    def test_started_during_has_records(self):
        self.assertEquals(
            Customer.objects.started_during(2013, 1).count(),
            12
        )

    def test_canceled_during(self):
        self.assertEquals(
            Customer.objects.canceled_during(2013, 4).count(),
            1
        )

    def test_canceled_all(self):
        self.assertEquals(
            Customer.objects.canceled().count(),
            1
        )

    def test_active_all(self):
        self.assertEquals(
            Customer.objects.active().count(),
            11
        )

    def test_started_plan_summary(self):
        for plan in Customer.objects.started_plan_summary_for(2013, 1):
            if plan["current_subscription__plan"] == "test":
                self.assertEquals(plan["count"], 11)
            if plan["current_subscription__plan"] == "test-2":
                self.assertEquals(plan["count"], 1)

    def test_active_plan_summary(self):
        for plan in Customer.objects.active_plan_summary():
            if plan["current_subscription__plan"] == "test":
                self.assertEquals(plan["count"], 10)
            if plan["current_subscription__plan"] == "test-2":
                self.assertEquals(plan["count"], 1)

    def test_canceled_plan_summary(self):
        for plan in Customer.objects.canceled_plan_summary_for(2013, 1):
            if plan["current_subscription__plan"] == "test":
                self.assertEquals(plan["count"], 1)
            if plan["current_subscription__plan"] == "test-2":
                self.assertEquals(plan["count"], 0)

    def test_churn(self):
        self.assertEquals(
            Customer.objects.churn(),
            decimal.Decimal("1") / decimal.Decimal("11")
        )


class TransferManagerTest(TestCase):

    def test_transfer_summary(self):
        event = Event.objects.create(
            stripe_id=TRANSFER_CREATED_TEST_DATA["id"],
            kind="transfer.created",
            livemode=True,
            webhook_message=TRANSFER_CREATED_TEST_DATA,
            validated_message=TRANSFER_CREATED_TEST_DATA,
            valid=True
        )
        event.process()
        event = Event.objects.create(
            stripe_id=TRANSFER_CREATED_TEST_DATA2["id"],
            kind="transfer.created",
            livemode=True,
            webhook_message=TRANSFER_CREATED_TEST_DATA2,
            validated_message=TRANSFER_CREATED_TEST_DATA2,
            valid=True
        )
        event.process()
        self.assertEquals(Transfer.objects.during(2012, 9).count(), 2)
        totals = Transfer.objects.paid_totals_for(2012, 9)
        self.assertEquals(
            totals["total_amount"], decimal.Decimal("19.10")
        )
        self.assertEquals(
            totals["total_net"], decimal.Decimal("19.10")
        )
        self.assertEquals(
            totals["total_charge_fees"], decimal.Decimal("0.90")
        )
        self.assertEquals(
            totals["total_adjustment_fees"], decimal.Decimal("0")
        )
        self.assertEquals(
            totals["total_refund_fees"], decimal.Decimal("0")
        )
        self.assertEquals(
            totals["total_validation_fees"], decimal.Decimal("0")
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
            fee=decimal.Decimal("3.42"),
            amount_refunded=decimal.Decimal("0")
        )
        Charge.objects.create(
            stripe_id="ch_2",
            customer=customer,
            charge_created=datetime.datetime(2013, 1, 1, tzinfo=timezone.utc),
            paid=True,
            amount=decimal.Decimal("100"),
            fee=decimal.Decimal("3.42"),
            amount_refunded=decimal.Decimal("10")
        )
        Charge.objects.create(
            stripe_id="ch_3",
            customer=customer,
            charge_created=datetime.datetime(2013, 1, 1, tzinfo=timezone.utc),
            paid=False,
            amount=decimal.Decimal("100"),
            fee=decimal.Decimal("3.42"),
            amount_refunded=decimal.Decimal("0")
        )
        Charge.objects.create(
            stripe_id="ch_4",
            customer=customer,
            charge_created=datetime.datetime(2013, 4, 1, tzinfo=timezone.utc),
            paid=True,
            amount=decimal.Decimal("500"),
            fee=decimal.Decimal("6.04"),
            amount_refunded=decimal.Decimal("15.42")
        )

    def test_charges_during(self):
        charges = Charge.objects.during(2013, 1)
        self.assertEqual(charges.count(), 3)

    def test_paid_totals_for_jan(self):
        totals = Charge.objects.paid_totals_for(2013, 1)
        self.assertEqual(totals["total_amount"], decimal.Decimal("200"))
        self.assertEqual(totals["total_fee"], decimal.Decimal("6.84"))
        self.assertEqual(totals["total_refunded"], decimal.Decimal("10"))

    def test_paid_totals_for_apr(self):
        totals = Charge.objects.paid_totals_for(2013, 4)
        self.assertEqual(totals["total_amount"], decimal.Decimal("500"))
        self.assertEqual(totals["total_fee"], decimal.Decimal("6.04"))
        self.assertEqual(totals["total_refunded"], decimal.Decimal("15.42"))

    def test_paid_totals_for_dec(self):
        totals = Charge.objects.paid_totals_for(2013, 12)
        self.assertEqual(totals["total_amount"], None)
        self.assertEqual(totals["total_fee"], None)
        self.assertEqual(totals["total_refunded"], None)
