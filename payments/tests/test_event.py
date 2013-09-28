# pylint: disable=C0301
from django.test import TestCase
from django.utils import timezone

from mock import patch, Mock

from ..models import Customer, Event, CurrentSubscription
from payments.signals import WEBHOOK_SIGNALS
from ..utils import get_user_model


class TestEventMethods(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser")
        self.user.save()
        self.customer = Customer.objects.create(
            stripe_id="cus_xxxxxxxxxxxxxxx",
            user=self.user
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

    @patch("stripe.Customer.retrieve")
    def test_process_customer_deleted(self, CustomerMock):
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
            validated_message=msg,
            valid=True
        )
        event.process()
        self.assertEquals(event.customer, self.customer)
        self.assertEquals(event.customer.user, None)

    @staticmethod
    def send_signal(customer, kind):
        event = Event(customer=customer, kind=kind)
        signal = WEBHOOK_SIGNALS.get(kind)
        signal.send(sender=Event, event=event)

    @staticmethod
    def connect_webhook_signal(kind, func, **kwargs):
        signal = WEBHOOK_SIGNALS.get(kind)
        signal.connect(func, **kwargs)

    @staticmethod
    def disconnect_webhook_signal(kind, func, **kwargs):
        signal = WEBHOOK_SIGNALS.get(kind)
        signal.disconnect(func, **kwargs)

    @patch("stripe.Customer.retrieve")
    def test_customer_subscription_deleted(self, CustomerMock):
        """
        Tests to make sure downstream signal handlers do not see stale CurrentSubscription object properties
        after a customer.subscription.deleted event occurs.  While the delete method is called
        on the affected CurrentSubscription object's properties are still accessible (unless the
        Customer object for the event gets refreshed before sending the complimentary signal)
        """
        kind = "customer.subscription.deleted"
        cs = CurrentSubscription(customer=self.customer, quantity=1, start=timezone.now(), amount=0)
        cs.save()
        customer = Customer.objects.get(pk=self.customer.pk)

        # Stripe objects will not have this attribute so we must delete it from the mocked object
        del customer.stripe_customer.subscription
        self.assertIsNotNone(customer.current_subscription)

        # This is the expected format of a customer.subscription.delete message
        msg = {
            "id": "evt_2eRjeAlnH1XMe8",
            "created": 1380317537,
            "livemode": True,
            "type": kind,
            "data": {
                "object": {
                    "id": "su_2ZDdGxJ3EQQc7Q",
                    "plan": {
                        "interval": "month",
                        "name": "xxx",
                        "amount": 200,
                        "currency": "usd",
                        "id": "xxx",
                        "object": "plan",
                        "livemode": True,
                        "interval_count": 1,
                        "trial_period_days": None
                    },
                    "object": "subscription",
                    "start": 1379111889,
                    "status": "canceled",
                    "customer": self.customer.stripe_id,
                    "cancel_at_period_end": False,
                    "current_period_start": 1378738246,
                    "current_period_end": 1381330246,
                    "ended_at": 1380317537,
                    "trial_start": None,
                    "trial_end": None,
                    "canceled_at": 1380317537,
                    "quantity": 1,
                    "application_fee_percent": None
                }
            },
            "object": "event",
            "pending_webhooks": 1,
            "request": "iar_2eRjQZmn0i3G9M"
        }

        # Create a test event for the message
        test_event = Event.objects.create(
            stripe_id=msg["id"],
            kind=kind,
            livemode=msg["livemode"],
            webhook_message=msg,
            validated_message=msg,
            valid=True,
            customer=customer,
        )

        def signal_handler(sender, event, **kwargs):
            # Illustrate and test what signal handlers would experience
            self.assertFalse(event.customer.current_subscription.is_valid())
            self.assertIsNone(event.customer.current_subscription.plan)
            self.assertIsNone(event.customer.current_subscription.status)
            self.assertIsNone(event.customer.current_subscription.id)

        signal_handler_mock = Mock()
        # Let's make the side effect call our real function, the mock is a proxy so we can assert it was called
        signal_handler_mock.side_effect = signal_handler
        TestEventMethods.connect_webhook_signal(kind, signal_handler_mock, weak=False, sender=Event)
        signal_handler_mock.reset_mock()

        # Now process the event - at the end of this the signal should get sent
        test_event.process()

        self.assertFalse(test_event.customer.current_subscription.is_valid())
        self.assertIsNone(test_event.customer.current_subscription.plan)
        self.assertIsNone(test_event.customer.current_subscription.status)
        self.assertIsNone(test_event.customer.current_subscription.id)

        # Verify our signal handler was called
        self.assertTrue(signal_handler_mock.called)

        TestEventMethods.disconnect_webhook_signal(kind, signal_handler_mock, weak=False, sender=Event)
