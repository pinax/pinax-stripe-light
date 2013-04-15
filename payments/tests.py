import datetime
import decimal
import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.utils import timezone

from django.contrib.auth.models import User

from mock import patch

from .models import convert_tstamp, Event, Customer, Transfer


class TestTimestampConversion(TestCase):
    
    def test_conversion_without_field_name(self):
        stamp = convert_tstamp(1365567407)
        self.assertEquals(
            stamp,
            datetime.datetime(2013, 4, 10, 4, 16, 47, tzinfo=timezone.utc)
        )
    
    def test_conversion_with_field_name(self):
        stamp = convert_tstamp({"my_date": 1365567407}, "my_date")
        self.assertEquals(
            stamp,
            datetime.datetime(2013, 4, 10, 4, 16, 47, tzinfo=timezone.utc)
        )
    
    def test_conversion_with_invalid_field_name(self):
        stamp = convert_tstamp({"my_date": 1365567407}, "foo")
        self.assertEquals(
            stamp,
            None
        )


class TestWebhook(TestCase):
    
    @patch("stripe.Event.retrieve")
    def test_webhook_with_transfer_event(self, StripeEventMock):
        data = {
            "created": 1348360173,
            "data": {
                "object": {
                    "amount": 455,
                    "currency": "usd",
                    "date": 1348876800,
                    "description": None,
                    "id": "ach_XXXXXXXXXXXX",
                    "object": "transfer",
                    "other_transfers": [],
                    "status": "pending",
                    "summary": {
                        "adjustment_count": 0,
                        "adjustment_fee_details": [],
                        "adjustment_fees": 0,
                        "adjustment_gross": 0,
                        "charge_count": 1,
                        "charge_fee_details": [{
                            "amount": 45,
                            "application": None,
                            "currency": "usd",
                            "description": None,
                            "type": "stripe_fee"
                        }],
                        "charge_fees": 45,
                        "charge_gross": 500,
                        "collected_fee_count": 0,
                        "collected_fee_gross": 0,
                        "currency": "usd",
                        "net": 455,
                        "refund_count": 0,
                        "refund_fees": 0,
                        "refund_gross": 0,
                        "validation_count": 0,
                        "validation_fees": 0
                    }
                }
            },
            "id": "evt_XXXXXXXXXXXXx",
            "livemode": True,
            "object": "event",
            "pending_webhooks": 1,
            "type": "transfer.created"
        }
        StripeEventMock.return_value.to_dict.return_value = data
        msg = json.dumps(data)
        resp = Client().post(
            reverse("payments_webhook"),
            msg,
            content_type="application/json"
        )
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(Event.objects.filter(kind="transfer.created").exists())


class TestTransferWebhooks(TestCase):
    
    def setUp(self):
        self.transfer_created_data = {
            "created": 1348360173,
            "data": {
                "object": {
                    "amount": 455,
                    "currency": "usd",
                    "date": 1348876800,
                    "description": None,
                    "id": "tr_XXXXXXXXXXXX",
                    "object": "transfer",
                    "other_transfers": [],
                    "status": "pending",
                    "summary": {
                        "adjustment_count": 0,
                        "adjustment_fee_details": [],
                        "adjustment_fees": 0,
                        "adjustment_gross": 0,
                        "charge_count": 1,
                        "charge_fee_details": [{
                            "amount": 45,
                            "application": None,
                            "currency": "usd",
                            "description": None,
                            "type": "stripe_fee"
                        }],
                        "charge_fees": 45,
                        "charge_gross": 500,
                        "collected_fee_count": 0,
                        "collected_fee_gross": 0,
                        "currency": "usd",
                        "net": 455,
                        "refund_count": 0,
                        "refund_fees": 0,
                        "refund_gross": 0,
                        "validation_count": 0,
                        "validation_fees": 0
                    }
                }
            },
            "id": "evt_XXXXXXXXXXXX",
            "livemode": True,
            "object": "event",
            "pending_webhooks": 1,
            "type": "transfer.created"
        }
    
    def test_transfer_created(self):
        event = Event.objects.create(
            stripe_id=self.transfer_created_data["id"],
            kind="transfer.created",
            livemode=True,
            webhook_message=self.transfer_created_data,
            validated_message=self.transfer_created_data,
            valid=True
        )
        event.process()
        transfer = Transfer.objects.get(stripe_id="tr_XXXXXXXXXXXX")
        self.assertEquals(transfer.amount, decimal.Decimal("4.55"))
        self.assertEquals(transfer.status, "pending")
    
    def test_transfer_paid_updates_existing_record(self):
        event = Event.objects.create(
            stripe_id=self.transfer_created_data["id"],
            kind="transfer.created",
            livemode=True,
            webhook_message=self.transfer_created_data,
            validated_message=self.transfer_created_data,
            valid=True
        )
        event.process()
        data = {
            "created": 1364658818,
            "data": {
                "object": {
                    "account": {
                        "bank_name": "BANK OF AMERICA, N.A.",
                        "country": "US",
                        "last4": "9999",
                        "object": "bank_account"
                    },
                    "amount": 455,
                    "currency": "usd",
                    "date": 1364601600,
                    "description": "STRIPE TRANSFER",
                    "fee": 0,
                    "fee_details": [],
                    "id": "tr_XXXXXXXXXXXX",
                    "livemode": True,
                    "object": "transfer",
                    "other_transfers": [],
                    "status": "paid",
                    "summary": {
                        "adjustment_count": 0,
                        "adjustment_fee_details": [],
                        "adjustment_fees": 0,
                        "adjustment_gross": 0,
                        "charge_count": 1,
                        "charge_fee_details": [{
                            "amount": 45,
                            "application": None,
                            "currency": "usd",
                            "description": None,
                            "type": "stripe_fee"
                        }],
                        "charge_fees": 45,
                        "charge_gross": 500,
                        "collected_fee_count": 0,
                        "collected_fee_gross": 0,
                        "collected_fee_refund_count": 0,
                        "collected_fee_refund_gross": 0,
                        "currency": "usd",
                        "net": 455,
                        "refund_count": 0,
                        "refund_fee_details": [],
                        "refund_fees": 0,
                        "refund_gross": 0,
                        "validation_count": 0,
                        "validation_fees": 0
                    },
                    "transactions": {
                        "count": 1,
                        "data": [{
                            "amount": 500,
                            "created": 1364064631,
                            "description": None,
                            "fee": 45,
                            "fee_details": [{
                                "amount": 45,
                                "application": None,
                                "currency": "usd",
                                "description": "Stripe processing fees",
                                "type": "stripe_fee"
                            }],
                            "id": "ch_XXXXXXXXXX",
                            "net": 455,
                            "type": "charge"
                        }],
                        "object": "list",
                        "url": "/v1/transfers/XX/transactions"
                    }
                }
            },
            "id": "evt_YYYYYYYYYYYY",
            "livemode": True,
            "object": "event",
            "pending_webhooks": 1,
            "type": "transfer.paid"
        }
        paid_event = Event.objects.create(
            stripe_id=data["id"],
            kind="transfer.paid",
            livemode=True,
            webhook_message=data,
            validated_message=data,
            valid=True
        )
        paid_event.process()
        transfer = Transfer.objects.get(stripe_id="tr_XXXXXXXXXXXX")
        self.assertEquals(transfer.status, "paid")


class TestCustomer(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username="patrick")
        self.customer = Customer.objects.create(
            user=self.user,
            stripe_id="cus_xxxxxxxxxxxxxxx",
            card_fingerprint="YYYYYYYY",
            card_last_4="2342",
            card_kind="Visa"
        )
    
    @patch("stripe.Customer.retrieve")
    def test_customer_purge_leaves_customer_record(self, CustomerRetrieveMock):
        self.customer.purge()
        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)
        self.assertTrue(customer.user is None)
        self.assertTrue(customer.card_fingerprint == "")
        self.assertTrue(customer.card_last_4 == "")
        self.assertTrue(customer.card_kind == "")
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())


class TestEventMethods(TestCase):
    
    def setUp(self):
        self.customer = Customer.objects.create(
            stripe_id="cus_xxxxxxxxxxxxxxx"
        )
    
    def test_link_customer_customer_created(self):
        msg = {
            "created": 1363911708,
            "data": {
                "object": {
                    "account_balance": 0,
                    "active_card": None,
                    "created": 1363911708,
                    "delinquent": False,
                    "description": None,
                    "discount": None,
                    "email": "xxxxxxxxxx@yahoo.com",
                    "id": "cus_xxxxxxxxxxxxxxx",
                    "livemode": True,
                    "object": "customer",
                    "subscription": None
                }
            },
            "id": "evt_xxxxxxxxxxxxx",
            "livemode": True,
            "object": "event",
            "pending_webhooks": 1,
            "type": "customer.created"
        }
        event = Event.objects.create(
            stripe_id=msg["id"],
            kind="customer.created",
            livemode=True,
            webhook_message=msg,
            validated_message=msg
        )
        event.link_customer()
        self.assertEquals(event.customer, self.customer)
    
    def test_link_customer_customer_updated(self):
        msg = {
            "created": 1346855599,
            "data": {
                "object": {
                    "account_balance": 0,
                    "active_card": {
                        "address_city": None,
                        "address_country": None,
                        "address_line1": None,
                        "address_line1_check": None,
                        "address_line2": None,
                        "address_state": None,
                        "address_zip": None,
                        "address_zip_check": None,
                        "country": "MX",
                        "cvc_check": "pass",
                        "exp_month": 1,
                        "exp_year": 2014,
                        "fingerprint": "XXXXXXXXXXX",
                        "last4": "7992",
                        "name": None,
                        "object": "card",
                        "type": "MasterCard"
                    },
                    "created": 1346855596,
                    "delinquent": False,
                    "description": None,
                    "discount": None,
                    "email": "xxxxxxxxxx@yahoo.com",
                    "id": "cus_xxxxxxxxxxxxxxx",
                    "livemode": True,
                    "object": "customer",
                    "subscription": None
                },
                "previous_attributes": {
                    "active_card": None
                }
            },
            "id": "evt_xxxxxxxxxxxxx",
            "livemode": True,
            "object": "event",
            "pending_webhooks": 1,
            "type": "customer.updated"
        }
        event = Event.objects.create(
            stripe_id=msg["id"],
            kind="customer.updated",
            livemode=True,
            webhook_message=msg,
            validated_message=msg
        )
        event.link_customer()
        self.assertEquals(event.customer, self.customer)
    
    def test_link_customer_customer_deleted(self):
        msg = {
            "created": 1348286560,
            "data": {
                "object": {
                    "account_balance": 0,
                    "active_card": None,
                    "created": 1348286302,
                    "delinquent": False,
                    "description": None,
                    "discount": None,
                    "email": "paltman+test@gmail.com",
                    "id": "cus_xxxxxxxxxxxxxxx",
                    "livemode": True,
                    "object": "customer",
                    "subscription": None
                }
            },
            "id": "evt_xxxxxxxxxxxxx",
            "livemode": True,
            "object": "event",
            "pending_webhooks": 1,
            "type": "customer.deleted"
        }
        event = Event.objects.create(
            stripe_id=msg["id"],
            kind="customer.deleted",
            livemode=True,
            webhook_message=msg,
            validated_message=msg
        )
        event.link_customer()
        self.assertEquals(event.customer, self.customer)
