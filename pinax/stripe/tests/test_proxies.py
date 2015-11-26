import decimal

from django.test import TestCase
from django.utils import timezone

from django.contrib.auth import get_user_model

import stripe

from mock import patch

from ..proxies import ChargeProxy, CustomerProxy, EventProxy


class ChargeProxyTests(TestCase):

    @patch("stripe.Charge.retrieve")
    def test_stripe_charge(self, RetrieveMock):
        ChargeProxy().stripe_charge
        self.assertTrue(RetrieveMock.called)

    def test_calculate_refund_amount(self):
        charge = ChargeProxy(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("50")
        actual = charge.calculate_refund_amount()
        self.assertEquals(expected, actual)

    def test_calculate_refund_amount_with_amount_under(self):
        charge = ChargeProxy(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("25")
        actual = charge.calculate_refund_amount(amount=decimal.Decimal("25"))
        self.assertEquals(expected, actual)

    def test_calculate_refund_amount_with_amount_over(self):
        charge = ChargeProxy(amount=decimal.Decimal("100"), amount_refunded=decimal.Decimal("50"))
        expected = decimal.Decimal("50")
        actual = charge.calculate_refund_amount(amount=decimal.Decimal("100"))
        self.assertEquals(expected, actual)


class CustomerProxyTests(TestCase):

    @patch("stripe.Customer.retrieve")
    def test_stripe_customer(self, RetrieveMock):
        CustomerProxy().stripe_customer
        self.assertTrue(RetrieveMock.called)

    def test_get_for_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        expected = CustomerProxy.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        actual = CustomerProxy.get_for_user(user)
        self.assertEquals(expected, actual)

    def test_get_for_user_not_exists(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        actual = CustomerProxy.get_for_user(user)
        self.assertIsNone(actual)

    @patch("stripe.Customer.retrieve")
    def test_purge(self, RetrieveMock):
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        customer = CustomerProxy.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        customer.purge()
        self.assertTrue(RetrieveMock().delete.called)
        self.assertIsNone(CustomerProxy.objects.get(stripe_id=customer.stripe_id).user)
        self.assertIsNotNone(CustomerProxy.objects.get(stripe_id=customer.stripe_id).date_purged)

    @patch("stripe.Customer.retrieve")
    def test_purge_already_deleted(self, RetrieveMock):
        RetrieveMock().delete.side_effect = stripe.InvalidRequestError("No such customer:", "error")
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        customer = CustomerProxy.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        customer.purge()
        self.assertTrue(RetrieveMock().delete.called)
        self.assertIsNone(CustomerProxy.objects.get(stripe_id=customer.stripe_id).user)
        self.assertIsNotNone(CustomerProxy.objects.get(stripe_id=customer.stripe_id).date_purged)

    @patch("stripe.Customer.retrieve")
    def test_purge_already_some_other_error(self, RetrieveMock):
        RetrieveMock().delete.side_effect = stripe.InvalidRequestError("Bad", "error")
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        customer = CustomerProxy.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        with self.assertRaises(stripe.InvalidRequestError):
            customer.purge()
        self.assertTrue(RetrieveMock().delete.called)
        self.assertIsNotNone(CustomerProxy.objects.get(stripe_id=customer.stripe_id).user)
        self.assertIsNone(CustomerProxy.objects.get(stripe_id=customer.stripe_id).date_purged)

    @patch("pinax.stripe.proxies.CustomerProxy.purge")
    def test_delete(self, PurgeMock):
        User = get_user_model()
        user = User.objects.create_user(
            username="patrick",
            email="paltman@eldarion.com"
        )
        customer = CustomerProxy.objects.create(
            user=user,
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
        customer.delete()
        self.assertTrue(PurgeMock.called)

    def test_can_charge(self):
        customer = CustomerProxy(default_source="card_001")
        self.assertTrue(customer.can_charge())

    def test_can_charge_false_purged(self):
        customer = CustomerProxy(default_source="card_001", date_purged=timezone.now())
        self.assertFalse(customer.can_charge())

    def test_can_charge_false_no_default_source(self):
        customer = CustomerProxy()
        self.assertFalse(customer.can_charge())

    def test_model_table_name(self):
        self.assertEquals(CustomerProxy()._meta.db_table, "pinax_stripe_customer")


class EventProxyTests(TestCase):

    def test_message(self):
        event = EventProxy(validated_message={"foo": 1})
        self.assertEquals(event.validated_message, event.message)

    def test_link_customer(self):
        CustomerProxy.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict(id="cu_123")))
        event = EventProxy.objects.create(validated_message=message, kind="customer.created")
        event.link_customer()
        self.assertEquals(event.customer.stripe_id, "cu_123")

    def test_link_customer_non_customer_event(self):
        CustomerProxy.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict(customer="cu_123")))
        event = EventProxy.objects.create(validated_message=message, kind="invoice.created")
        event.link_customer()
        self.assertEquals(event.customer.stripe_id, "cu_123")

    def test_link_customer_no_customer(self):
        CustomerProxy.objects.create(stripe_id="cu_123")
        message = dict(data=dict(object=dict()))
        event = EventProxy.objects.create(validated_message=message, kind="transfer.created")
        event.link_customer()
        self.assertIsNone(event.customer, "cu_123")

    def test_link_customer_does_not_exist(self):
        message = dict(data=dict(object=dict(id="cu_123")))
        event = EventProxy.objects.create(validated_message=message, kind="customer.created")
        event.link_customer()
        self.assertIsNone(event.customer)
