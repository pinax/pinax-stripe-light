import decimal

from django.test import TestCase

from django.contrib.auth import get_user_model

from mock import patch, PropertyMock, Mock

from ..actions import refunds, customers, syncs, charges
from ..proxies import CustomerProxy, ChargeProxy, SubscriptionProxy, PlanProxy


class TestCustomer(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        self.customer = CustomerProxy.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        self.plan = PlanProxy.objects.create(
            stripe_id="p1",
            amount=10,
            currency="usd",
            interval="monthly",
            interval_count=1,
            name="Pro"
        )
        self.subscription = SubscriptionProxy.objects.create(
            customer=self.customer,
            plan=self.plan,
            stripe_id="su_123",
            quantity=1,
            start="2015-01-01"
        )

    def test_model_table_name(self):
        self.assertEquals(CustomerProxy()._meta.db_table, "pinax_stripe_customer")

    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_customer_create_user_only(self, CreateMock, RetrieveMock):
        self.customer.delete()
        cu = CreateMock()
        cu.account_balance = 0
        cu.delinquent = False
        cu.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
        cu.currency = "usd"
        cu.id = "cus_XXXXX"
        customer = customers.create(self.user)
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_XXXXX")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertIsNone(kwargs["source"])
        self.assertIsNone(kwargs["plan"])
        self.assertIsNone(kwargs["trial_end"])

    @patch("stripe.Invoice.create")
    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_customer_create_user_with_plan(self, CreateMock, RetrieveMock, InvoiceMock):
        self.customer.delete()
        PlanProxy.objects.create(
            stripe_id="pro-monthly",
            name="Pro ($19.99/month)",
            amount=19.99,
            interval="monthly",
            interval_count=1,
            currency="usd"
        )
        type(InvoiceMock()).amount_due = PropertyMock(return_value=3)
        cu = CreateMock()
        cu.account_balance = 0
        cu.delinquent = False
        cu.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
        cu.currency = "usd"
        cu.id = "cus_YYYYYYYYYYYYY"
        subscription = Mock()
        subscription.plan.id = "pro-monthly"
        subscription.current_period_start = 1348876800
        subscription.current_period_end = 1349876800
        subscription.canceled_at = 1349876800
        subscription.ended_at = 1349876800
        subscription.application_fee_percent = 0
        subscription.plan.amount = 9999
        subscription.plan.currency = "usd"
        subscription.status = "active"
        subscription.cancel_at_period_end = False
        subscription.start = 1348876800
        subscription.quantity = 1
        subscription.trial_start = 1348876800
        subscription.trial_end = 1349876800
        subscription.id = "su_YYYYYYYYYYYYY"
        cu.subscriptions.data = [subscription]
        rm = RetrieveMock()
        rm.id = "cus_YYYYYYYYYYYYY"
        rm.account_balance = 0
        rm.delinquent = False
        rm.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
        rm.currency = "usd"
        rm.subscription.plan.id = "pro-monthly"
        rm.subscriptions.data = [subscription]
        customer = customers.create(self.user, card="token232323", plan=self.plan)
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_YYYYYYYYYYYYY")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertEqual(kwargs["source"], "token232323")
        self.assertEqual(kwargs["plan"], self.plan)
        self.assertIsNotNone(kwargs["trial_end"])
        self.assertTrue(InvoiceMock.called)
        self.assertTrue(customer.subscription_set.all()[0].plan, "pro")
    #
    # @patch("stripe.Customer.retrieve")
    # def test_customer_subscribe_with_specified_quantity(self, CustomerRetrieveMock):
    #     cu = CustomerRetrieveMock()
    #     cu.account_balance = 0
    #     cu.delinquent = False
    #     cu.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
    #     cu.currency = "usd"
    #     cu.id = "cus_YYYYYYYYYYYYY"
    #     subscription = Mock()
    #     subscription.plan.id = "pro-monthly"
    #     subscription.current_period_start = 1348876800
    #     subscription.current_period_end = 1349876800
    #     subscription.plan.amount = 9999
    #     subscription.plan.currency = "usd"
    #     subscription.status = "active"
    #     subscription.cancel_at_period_end = False
    #     subscription.start = 1348876800
    #     subscription.quantity = 1
    #     subscription.trial_start = 1348876800
    #     subscription.trial_end = 1349876800
    #     subscription.id = "su_YYYYYYYYYYYYY"
    #     cu.subscriptions.data = [subscription]
    #     subscriptions.update(subscriptions.current_subscription(self.customer), "entry", quantity=3, charge_immediately=False)
    #     _, kwargs = customer.update_subscription.call_args
    #     self.assertEqual(kwargs["quantity"], 3)
    #
    # @patch("stripe.Customer.retrieve")
    # def test_customer_subscribe_with_callback_quantity(self, CustomerRetrieveMock):
    #     cu = CustomerRetrieveMock()
    #     cu.account_balance = 0
    #     cu.delinquent = False
    #     cu.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
    #     cu.currency = "usd"
    #     cu.id = "cus_YYYYYYYYYYYYY"
    #     subscription = Mock()
    #     subscription.plan.id = "pro-monthly"
    #     subscription.current_period_start = 1348876800
    #     subscription.current_period_end = 1349876800
    #     subscription.plan.amount = 9999
    #     subscription.plan.currency = "usd"
    #     subscription.status = "active"
    #     subscription.cancel_at_period_end = False
    #     subscription.start = 1348876800
    #     subscription.quantity = 1
    #     subscription.trial_start = 1348876800
    #     subscription.trial_end = 1349876800
    #     subscription.id = "su_YYYYYYYYYYYYY"
    #     cu.subscriptions.data = [subscription]
    #     subscriptions.create(self.customer, "entry", charge_immediately=False)
    #     _, kwargs = customer.update_subscription.call_args
    #     self.assertEqual(kwargs["quantity"], 4)

    @patch("stripe.Customer.retrieve")
    def test_customer_purge_leaves_customer_record(self, CustomerRetrieveMock):
        self.customer.purge()
        customer = CustomerProxy.objects.get(stripe_id=self.customer.stripe_id)
        self.assertTrue(customer.user is None)
        self.assertTrue(self.User.objects.filter(pk=self.user.pk).exists())

    @patch("stripe.Customer.retrieve")
    def test_customer_delete_same_as_purge(self, CustomerRetrieveMock):
        self.customer.delete()
        customer = CustomerProxy.objects.get(stripe_id=self.customer.stripe_id)
        self.assertTrue(customer.user is None)
        self.assertTrue(self.User.objects.filter(pk=self.user.pk).exists())

    @patch("stripe.Customer.retrieve")
    def test_customer_sync_updates_credit_card(self, StripeCustomerRetrieveMock):
        """
        Test to make sure Customer.sync will update a credit card when there is a new card
        """
        cu = StripeCustomerRetrieveMock()
        cu.account_balance = 0
        cu.delinquent = False
        cu.default_source = "card_178Zqj2eZvKYlo2Cr2fUZZz7"
        cu.currency = "usd"

        class SourceMock(dict):
            def __init__(self):
                self.update(dict(
                    id="card_178Zqj2eZvKYlo2Cr2fUZZz7",
                    object="card",
                    address_city=None,
                    address_country=None,
                    address_line1=None,
                    address_line1_check=None,
                    address_line2=None,
                    address_state=None,
                    address_zip=None,
                    address_zip_check=None,
                    brand="Visa",
                    country="US",
                    customer="cus_7NKVEhB90BjhvB",
                    cvc_check="pass",
                    dynamic_last4=None,
                    exp_month=4,
                    exp_year=2040,
                    funding="credit",
                    fingerprint="",
                    last4="4242",
                    metadata={},
                    name=None,
                    tokenization_method=None
                ))
        source = SourceMock()
        cu.sources.data = [source]
        customer = CustomerProxy.objects.get(stripe_id=self.customer.stripe_id)

        self.assertNotEqual(customer.card_set.count(), 1)

        syncs.sync_customer(customer)

        # Reload saved customer
        customer = CustomerProxy.objects.get(stripe_id=self.customer.stripe_id)

        self.assertEquals(customer.card_set.count(), 1)

    def test_change_charge(self):
        self.assertTrue(self.customer.can_charge())

    @patch("stripe.Customer.retrieve")
    def test_cannot_charge(self, CustomerRetrieveMock):
        self.customer.delete()
        self.assertFalse(self.customer.can_charge())

    def test_charge_accepts_only_decimals(self):
        with self.assertRaises(ValueError):
            charges.create(customer=self.customer, amount=10)

    @patch("stripe.Refund.create")
    @patch("stripe.Charge.retrieve")
    def test_refund_charge(self, RetrieveMock, RefundMock):
        charge = ChargeProxy.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            source="card_01",
            amount=decimal.Decimal("10.00"),
            currency="usd",
            paid=True,
            refunded=False,
            disputed=False
        )

        class ChargeMock(dict):
            def __init__(self):
                self.update({
                    "id": "ch_XXXXXX",
                    "source": {
                        "id": "card_01"
                    },
                    "amount": 1000,
                    "currency": "usd",
                    "paid": True,
                    "refunded": True,
                    "captured": True,
                    "invoice": None,
                    "amount_refunded": 1000,
                    "dispute": None,
                    "created": 1363911708,
                    "customer": "cus_xxxxxxxxxxxxxxx"
                })

            def refund(self, amount):
                return self

        RetrieveMock.return_value = ChargeMock()

        refunds.create(charge)
        charge2 = ChargeProxy.objects.get(stripe_id="ch_XXXXXX")
        self.assertEquals(charge2.refunded, True)
        self.assertEquals(charge2.amount_refunded, decimal.Decimal("10.00"))

    def test_calculate_refund_amount_full_refund(self):
        charge = ChargeProxy(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00"),
            currency="usd",
        )
        self.assertEquals(
            charge.calculate_refund_amount(),
            500
        )

    def test_calculate_refund_amount_partial_refund(self):
        charge = ChargeProxy(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00"),
            currency="usd",
        )
        self.assertEquals(
            charge.calculate_refund_amount(amount=decimal.Decimal("300.00")),
            300
        )

    def test_calculate_refund_above_max_refund(self):
        charge = ChargeProxy(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00"),
            currency="usd",
        )
        self.assertEquals(
            charge.calculate_refund_amount(amount=decimal.Decimal("600.00")),
            500
        )

    @patch("stripe.Charge.retrieve")
    @patch("stripe.Charge.create")
    def test_charge_converts_dollars_into_cents(self, ChargeMock, RetrieveMock):
        ChargeMock.return_value.id = "ch_XXXXX"
        RetrieveMock.return_value = {
            "id": "ch_XXXXXX",
            "source": {
                "id": "card_01"
            },
            "amount": 1000,
            "currency": "usd",
            "paid": True,
            "refunded": False,
            "captured": True,
            "invoice": None,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        charges.create(customer=self.customer, amount=decimal.Decimal("10.00"), currency="usd")
        _, kwargs = ChargeMock.call_args
        self.assertEquals(kwargs["amount"], 1000)

    def test_record_charge_in_jpy_with(self):
        data = {
            "id": "ch_XXXXXX",
            "source": {
                "id": "card_01"
            },
            "amount": 1000,
            "currency": "jpy",
            "paid": True,
            "refunded": False,
            "captured": True,
            "invoice": None,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        obj = syncs.sync_charge_from_stripe_data(data)
        self.assertEquals(ChargeProxy.objects.get(stripe_id="ch_XXXXXX").pk, obj.pk)
        self.assertEquals(obj.paid, True)
        self.assertEquals(obj.disputed, False)
        self.assertEquals(obj.refunded, False)
        self.assertEquals(obj.amount_refunded, None)
        self.assertEquals(obj.amount, decimal.Decimal("1000"))

    @patch("stripe.Refund.create")
    @patch("stripe.Charge.retrieve")
    def test_refund_charge_in_jpy(self, RetrieveMock, RefundMock):
        charge = ChargeProxy.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            source="card_01",
            amount=decimal.Decimal("1000.00"),
            currency="jpy",
            paid=True,
            refunded=False,
            captured=True,
            disputed=False
        )

        class ChargeMock(dict):
            def __init__(self):
                self.update({
                    "id": "ch_XXXXXX",
                    "source": {
                        "id": "card_01"
                    },
                    "amount": 1000,
                    "currency": "jpy",
                    "paid": True,
                    "refunded": True,
                    "invoice": None,
                    "amount_refunded": 1000,
                    "captured": True,
                    "dispute": None,
                    "created": 1363911708,
                    "customer": "cus_xxxxxxxxxxxxxxx"
                })

            def refund(self, amount):
                return self

        RetrieveMock.return_value = ChargeMock()
        refunds.create(charge)
        charge2 = ChargeProxy.objects.get(stripe_id="ch_XXXXXX")
        self.assertEquals(charge2.refunded, True)
        self.assertEquals(charge2.amount_refunded, decimal.Decimal("1000.00"))

    def test_calculate_refund_amount_full_refund_in_jpy(self):
        charge = ChargeProxy(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00"),
            currency="jpy",
        )
        self.assertEquals(
            charge.calculate_refund_amount(),
            500
        )

    def test_calculate_refund_amount_partial_refund_in_jpy(self):
        charge = ChargeProxy(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00"),
            currency="jpy",
        )
        self.assertEquals(
            charge.calculate_refund_amount(amount=decimal.Decimal("300.00")),
            300
        )

    def test_calculate_refund_above_max_refund_in_jpy(self):
        charge = ChargeProxy(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00"),
            currency="jpy",
        )
        self.assertEquals(
            charge.calculate_refund_amount(amount=decimal.Decimal("600.00")),
            500
        )

    @patch("stripe.Charge.retrieve")
    @patch("stripe.Charge.create")
    def test_charge_do_not_converts_dollars_in_jpy(self, ChargeMock, RetrieveMock):
        ChargeMock.return_value.id = "ch_XXXXX"
        RetrieveMock.return_value = {
            "id": "ch_XXXXXX",
            "source": {
                "id": "card_01"
            },
            "amount": 1000,
            "currency": "jpy",
            "paid": True,
            "refunded": False,
            "captured": True,
            "invoice": None,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        charges.create(customer=self.customer, amount=decimal.Decimal("1000.00"), currency="jpy")
        _, kwargs = ChargeMock.call_args
        self.assertEquals(kwargs["amount"], 1000)
