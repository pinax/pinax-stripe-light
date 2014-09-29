# pylint: disable=C0301
import decimal

from django.test import TestCase

from mock import patch, PropertyMock, Mock

from ..models import Customer, Charge
from ..signals import card_changed
from ..utils import get_user_model


class TestCustomer(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx",
            card_fingerprint="YYYYYYYY",
            card_last_4="2342",
            card_kind="Visa"
        )

    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_customer_create_user_only(self, CreateMock, RetrieveMock):
        self.customer.delete()
        stripe_customer = CreateMock()
        stripe_customer.active_card = None
        stripe_customer.subscription = None
        stripe_customer.id = "cus_YYYYYYYYYYYYY"
        customer = Customer.create(self.user)
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_YYYYYYYYYYYYY")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertIsNone(kwargs["card"])
        self.assertIsNone(kwargs["plan"])
        self.assertIsNone(kwargs["trial_end"])

    @patch("stripe.Invoice.create")
    @patch("stripe.Customer.retrieve")
    @patch("stripe.Customer.create")
    def test_customer_create_user_with_plan(self, CreateMock, RetrieveMock, InvoiceMock):
        self.customer.delete()
        type(InvoiceMock()).amount_due = PropertyMock(return_value=3)
        stripe_customer = CreateMock()
        stripe_customer.active_card = None
        stripe_customer.subscription.plan.id = "pro-monthly"
        stripe_customer.subscription.current_period_start = 1348876800
        stripe_customer.subscription.current_period_end = 1349876800
        stripe_customer.subscription.plan.amount = 9999
        stripe_customer.subscription.plan.currency = "usd"
        stripe_customer.subscription.status = "active"
        stripe_customer.subscription.cancel_at_period_end = False
        stripe_customer.subscription.start = 1348876800
        stripe_customer.subscription.quantity = 1
        stripe_customer.subscription.trial_start = 1348876800
        stripe_customer.subscription.trial_end = 1349876800
        stripe_customer.id = "cus_YYYYYYYYYYYYY"
        customer = Customer.create(self.user, card="token232323", plan="pro")
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.stripe_id, "cus_YYYYYYYYYYYYY")
        _, kwargs = CreateMock.call_args
        self.assertEqual(kwargs["email"], self.user.email)
        self.assertEqual(kwargs["card"], "token232323")
        self.assertEqual(kwargs["plan"], "pro-monthly")
        self.assertIsNotNone(kwargs["trial_end"])
        self.assertTrue(InvoiceMock.called)
        self.assertTrue(customer.current_subscription.plan, "pro")

    # @@@ Need to figure out a way to temporarily set DEFAULT_PLAN to "entry" for this test
    # @patch("stripe.Invoice.create")
    # @patch("stripe.Customer.retrieve")
    # @patch("stripe.Customer.create")
    # def test_customer_create_user_with_card_default_plan(self, CreateMock, RetrieveMock, PayMock):
    #     self.customer.delete()
    #     stripe_customer = CreateMock()
    #     stripe_customer.active_card = None
    #     stripe_customer.subscription.plan.id = "entry-monthly"
    #     stripe_customer.subscription.current_period_start = 1348876800
    #     stripe_customer.subscription.current_period_end = 1349876800
    #     stripe_customer.subscription.plan.amount = 9999
    #     stripe_customer.subscription.status = "active"
    #     stripe_customer.subscription.cancel_at_period_end = False
    #     stripe_customer.subscription.start = 1348876800
    #     stripe_customer.subscription.quantity = 1
    #     stripe_customer.subscription.trial_start = 1348876800
    #     stripe_customer.subscription.trial_end = 1349876800
    #     stripe_customer.id = "cus_YYYYYYYYYYYYY"
    #     customer = Customer.create(self.user, card="token232323")
    #     self.assertEqual(customer.user, self.user)
    #     self.assertEqual(customer.stripe_id, "cus_YYYYYYYYYYYYY")
    #     _, kwargs = CreateMock.call_args
    #     self.assertEqual(kwargs["email"], self.user.email)
    #     self.assertEqual(kwargs["card"], "token232323")
    #     self.assertEqual(kwargs["plan"], "entry-monthly")
    #     self.assertIsNotNone(kwargs["trial_end"])
    #     self.assertTrue(PayMock.called)
    #     self.assertTrue(customer.current_subscription.plan, "entry")

    @patch("stripe.Customer.retrieve")
    def test_customer_subscribe_with_specified_quantity(self, CustomerRetrieveMock):
        customer = CustomerRetrieveMock()
        customer.subscription.plan.id = "entry-monthly"
        customer.subscription.current_period_start = 1348360173
        customer.subscription.current_period_end = 1375603198
        customer.subscription.plan.amount = decimal.Decimal("9.57")
        customer.subscription.status = "active"
        customer.subscription.cancel_at_period_end = True
        customer.subscription.start = 1348360173
        customer.subscription.quantity = 1
        customer.subscription.trial_start = None
        customer.subscription.trial_end = None
        self.customer.subscribe("entry", quantity=3, charge_immediately=False)
        _, kwargs = customer.update_subscription.call_args
        self.assertEqual(kwargs["quantity"], 3)

    @patch("stripe.Customer.retrieve")
    def test_customer_subscribe_with_callback_quantity(self, CustomerRetrieveMock):
        customer = CustomerRetrieveMock()
        customer.subscription.plan.id = "entry-monthly"
        customer.subscription.current_period_start = 1348360173
        customer.subscription.current_period_end = 1375603198
        customer.subscription.plan.amount = decimal.Decimal("9.57")
        customer.subscription.status = "active"
        customer.subscription.cancel_at_period_end = True
        customer.subscription.start = 1348360173
        customer.subscription.quantity = 1
        customer.subscription.trial_start = None
        customer.subscription.trial_end = None
        self.customer.subscribe("entry", charge_immediately=False)
        _, kwargs = customer.update_subscription.call_args
        self.assertEqual(kwargs["quantity"], 4)

    @patch("stripe.Customer.retrieve")
    def test_customer_purge_leaves_customer_record(self, CustomerRetrieveMock):
        self.customer.purge()
        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)
        self.assertTrue(customer.user is None)
        self.assertTrue(customer.card_fingerprint == "")
        self.assertTrue(customer.card_last_4 == "")
        self.assertTrue(customer.card_kind == "")
        self.assertTrue(self.User.objects.filter(pk=self.user.pk).exists())

    @patch("stripe.Customer.retrieve")
    def test_customer_delete_same_as_purge(self, CustomerRetrieveMock):
        self.customer.delete()
        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)
        self.assertTrue(customer.user is None)
        self.assertTrue(customer.card_fingerprint == "")
        self.assertTrue(customer.card_last_4 == "")
        self.assertTrue(customer.card_kind == "")
        self.assertTrue(self.User.objects.filter(pk=self.user.pk).exists())

    @patch("stripe.Customer.retrieve")
    def test_customer_sync_updates_credit_card(self, StripeCustomerRetrieveMock):
        """
        Test to make sure Customer.sync will update a credit card when there is a new card
        """
        StripeCustomerRetrieveMock.return_value.active_card.fingerprint = "FINGERPRINT"
        StripeCustomerRetrieveMock.return_value.active_card.type = "DINERS"
        StripeCustomerRetrieveMock.return_value.active_card.last4 = "BEEF"

        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)

        self.assertNotEqual(customer.card_fingerprint, customer.stripe_customer.active_card.fingerprint)
        self.assertNotEqual(customer.card_last_4, customer.stripe_customer.active_card.last4)
        self.assertNotEqual(customer.card_kind, customer.stripe_customer.active_card.type)

        customer.sync()

        # Reload saved customer
        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)

        self.assertEqual(customer.card_fingerprint, customer.stripe_customer.active_card.fingerprint)
        self.assertEqual(customer.card_last_4, customer.stripe_customer.active_card.last4)
        self.assertEqual(customer.card_kind, customer.stripe_customer.active_card.type)

    @patch("stripe.Customer.retrieve")
    def test_customer_sync_does_not_update_credit_card(self, StripeCustomerRetrieveMock):
        """
        Test to make sure Customer.sync will not update a credit card when there are no changes
        """
        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)

        StripeCustomerRetrieveMock.return_value.active_card.fingerprint = customer.card_fingerprint
        StripeCustomerRetrieveMock.return_value.active_card.type = customer.card_kind
        StripeCustomerRetrieveMock.return_value.active_card.last4 = customer.card_last_4

        self.assertEqual(customer.card_fingerprint, customer.stripe_customer.active_card.fingerprint)
        self.assertEqual(customer.card_last_4, customer.stripe_customer.active_card.last4)
        self.assertEqual(customer.card_kind, customer.stripe_customer.active_card.type)

        customer.sync()

        self.assertEqual(customer.card_fingerprint, customer.stripe_customer.active_card.fingerprint)
        self.assertEqual(customer.card_last_4, customer.stripe_customer.active_card.last4)
        self.assertEqual(customer.card_kind, customer.stripe_customer.active_card.type)

    @patch("stripe.Customer.retrieve")
    def test_customer_sync_removes_credit_card(self, StripeCustomerRetrieveMock):
        """
        Test to make sure Customer.sync removes credit card when there is no active card
        """
        def _perform_test(kitchen):
            kitchen.sync()

            # Reload saved customer
            cus = Customer.objects.get(stripe_id=self.customer.stripe_id)

            # Test to make sure card details were removed
            self.assertEqual(cus.card_fingerprint, "")
            self.assertEqual(cus.card_last_4, "")
            self.assertEqual(cus.card_kind, "")

        StripeCustomerRetrieveMock.return_value.active_card = None

        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)
        _perform_test(customer)

        # Test removal of attribute for active_card so hasattr will fail

        # Add back credit card to the customer
        self.test_customer_sync_updates_credit_card()

        # Reload saved customer
        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)
        # Remove the credit card from the mocked object
        del customer.stripe_customer.active_card

        _perform_test(customer)

    def test_customer_sync_sends_credit_card_updated_signal(self):
        """
        Test to make sure the card_changed signal gets sent when there is an updated credit card during sync
        """
        mocked_func = Mock()
        card_changed.connect(mocked_func, weak=False)

        mocked_func.reset_mock()
        self.test_customer_sync_updates_credit_card()
        # Make sure the signal was called
        self.assertTrue(mocked_func.called)

        mocked_func.reset_mock()
        self.test_customer_sync_removes_credit_card()
        # Make sure the signal was called
        self.assertTrue(mocked_func.called)

        card_changed.disconnect(mocked_func, weak=False)

    def test_customer_sync_does_not_send_credit_card_updated_signal(self):
        """
        Test to make sure the card_changed signal does not get sent when there is no change to the credit card during sync
        """
        mocked_func = Mock()
        card_changed.connect(mocked_func, weak=False)
        mocked_func.reset_mock()
        self.test_customer_sync_does_not_update_credit_card()
        # Make sure the signal was not called
        self.assertFalse(mocked_func.called)
        card_changed.disconnect(mocked_func, weak=False)

    def test_change_charge(self):
        self.assertTrue(self.customer.can_charge())

    @patch("stripe.Customer.retrieve")
    def test_cannot_charge(self, CustomerRetrieveMock):
        self.customer.delete()
        self.assertFalse(self.customer.can_charge())

    def test_charge_accepts_only_decimals(self):
        with self.assertRaises(ValueError):
            self.customer.charge(10)

    @patch("stripe.Charge.retrieve")
    def test_record_charge(self, RetrieveMock):
        RetrieveMock.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "currency": "usd",
            "paid": True,
            "refunded": False,
            "captured": True,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        obj = self.customer.record_charge("ch_XXXXXX")
        self.assertEquals(Charge.objects.get(stripe_id="ch_XXXXXX").pk, obj.pk)
        self.assertEquals(obj.paid, True)
        self.assertEquals(obj.disputed, False)
        self.assertEquals(obj.refunded, False)
        self.assertEquals(obj.amount_refunded, None)

    @patch("stripe.Charge.retrieve")
    def test_refund_charge(self, RetrieveMock):
        charge = Charge.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            card_last_4="4323",
            card_kind="Visa",
            amount=decimal.Decimal("10.00"),
            currency="usd",
            paid=True,
            refunded=False,
            fee=decimal.Decimal("4.99"),
            disputed=False
        )
        RetrieveMock.return_value.refund.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "currency": "usd",
            "paid": True,
            "refunded": True,
            "captured": True,
            "amount_refunded": 1000,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        charge.refund()
        charge2 = Charge.objects.get(stripe_id="ch_XXXXXX")
        self.assertEquals(charge2.refunded, True)
        self.assertEquals(charge2.amount_refunded, decimal.Decimal("10.00"))

    def test_calculate_refund_amount_full_refund(self):
        charge = Charge(
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
        charge = Charge(
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
        charge = Charge(
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
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "currency": "usd",
            "paid": True,
            "refunded": False,
            "captured": True,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        self.customer.charge(
            amount=decimal.Decimal("10.00"),
            currency="usd"
        )
        _, kwargs = ChargeMock.call_args
        self.assertEquals(kwargs["amount"], 1000)

    @patch("stripe.Charge.retrieve")
    def test_record_charge_in_jpy_with(self, RetrieveMock):
        RetrieveMock.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "currency": "jpy",
            "paid": True,
            "refunded": False,
            "captured": True,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        obj = self.customer.record_charge("ch_XXXXXX")
        self.assertEquals(Charge.objects.get(stripe_id="ch_XXXXXX").pk, obj.pk)
        self.assertEquals(obj.paid, True)
        self.assertEquals(obj.disputed, False)
        self.assertEquals(obj.refunded, False)
        self.assertEquals(obj.amount_refunded, None)
        self.assertEquals(obj.amount, decimal.Decimal("1000"))

    @patch("stripe.Charge.retrieve")
    def test_refund_charge_in_jpy(self, RetrieveMock):
        charge = Charge.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            card_last_4="4323",
            card_kind="Visa",
            amount=decimal.Decimal("1000.00"),
            currency="jpy",
            paid=True,
            refunded=False,
            captured=True,
            fee=decimal.Decimal("4.99"),
            disputed=False
        )
        RetrieveMock.return_value.refund.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "currency": "jpy",
            "paid": True,
            "refunded": True,
            "amount_refunded": 1000,
            "fee": 499,
            "captured": True,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        charge.refund()
        charge2 = Charge.objects.get(stripe_id="ch_XXXXXX")
        self.assertEquals(charge2.refunded, True)
        self.assertEquals(charge2.amount_refunded, decimal.Decimal("1000.00"))

    def test_calculate_refund_amount_full_refund_in_jpy(self):
        charge = Charge(
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
        charge = Charge(
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
        charge = Charge(
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
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "currency": "jpy",
            "paid": True,
            "refunded": False,
            "captured": True,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        self.customer.charge(
            amount=decimal.Decimal("1000.00"),
            currency="jpy"
        )
        _, kwargs = ChargeMock.call_args
        self.assertEquals(kwargs["amount"], 1000)
