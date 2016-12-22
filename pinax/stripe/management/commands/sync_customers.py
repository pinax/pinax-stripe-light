"""Update our cached data using stripe data."""

from django.core.management.base import BaseCommand

from pinax.stripe.actions import charges
from pinax.stripe.actions import customers
from pinax.stripe.actions import invoices
from pinax.stripe.actions import plans
from pinax.stripe.models import Customer
from pinax.stripe.models import Plan

import stripe


class StripeIterator(object):
    """Iterator over Stripe collection with extra context."""

    def __init__(self, cls):
        """Fetch total and setup iterator."""
        self.count = 0
        collection = cls.list(
            include=['total_count'],
            limit=1
        )
        self.total = collection.total_count
        self.iterator = cls.list(
            limit=100
        ).auto_paging_iter()

    def __iter__(self):
        """Self is the iterator."""
        return self

    def next(self):
        """Return internal iterator and extra context."""
        self.count += 1
        return (
            self.iterator.next(),
            self.count,
            self.total,
            int(round(100 * (float(self.count) / float(self.total))))
        )


def _sync_customers():
    created = 0
    synced = 0
    for obj, count, total, perc in StripeIterator(stripe.Customer):
        try:
            customer_obj = Customer.objects.select_related(
                'user'
            ).get(stripe_id=obj.id)
        except Customer.DoesNotExist:
            customer_obj = Customer.objects.create(
                user=None,
                stripe_id=obj.id
            )
            created += 1
        try:
            customers.sync_customer(
                customer_obj, obj
            )
        except Plan.DoesNotExist:
            print 'Plan subscribed to by customer {} not found, skipping customer.'.format(
                customer_obj.stripe_id
            )

        synced += 1
        username = getattr(
            customer_obj.user,
            customer_obj.user.USERNAME_FIELD
        ) if customer_obj.user_id else 'Unlinked'
        print("[{0}/{1} {2}%] Syncing customer {3} [{4}]".format(
            count, total, perc, username, customer_obj.user_id
        ))
    return created, synced


def _sync_charges():
    synced = 0
    skipped = 0
    for obj, count, total, perc in StripeIterator(stripe.Charge):
        try:
            charges.sync_charge_from_stripe_data(obj)
            synced += 1
        except Customer.DoesNotExist:
            print("Warning: stripe customer did not exist for charge: {}".format(
                obj.id
            ))
            skipped += 1
        print("[{0}/{1} {2}%] Syncing charge {3}".format(
            count, total, perc, obj.id
        ))
    return synced, skipped


def _sync_invoices():
    synced = 0
    skipped = 0
    plans.sync_plans()
    for obj, count, total, perc in StripeIterator(stripe.Invoice):
        try:
            invoices.sync_invoice_from_stripe_data(
                obj,
                send_receipt=False
            )
            synced += 1
        except Customer.DoesNotExist:
            message = "invoice skipped: stripe customer did not exist for invoice: {}".format(
                obj.id
            )
            skipped += 1
        except Plan.DoesNotExist:
            message = "invoice skipped: stripe plan did not exist for invoice: {}".format(
                obj.id
            )
            skipped += 1
        except stripe.InvalidRequestError as se:
            message = "invoice skipped: {}: {}".format(
                obj.id, se.message
            )
            skipped += 1
        else:
            message = "synced invoice {}".format(
                obj.id
            )
        print("[{0}/{1} {2}%] {3}".format(
            count, total, perc, message
        ))
    return synced, skipped


class Command(BaseCommand):
    """Sync customer data."""

    help = "Sync customer data"

    def handle(self, *args, **options):
        """Slurp dem records."""
        customers_created, customers_synced = (
            _sync_customers()
        )
        charges_synced, charges_skipped = (
            _sync_charges()
        )
        invoices_synced, invoices_skipped = (
            _sync_invoices()
        )
        print("""==== Sync Report ====
Customers: {} synced ({} created)
Charges: {} synced ({} skipped due to missing customer)
Invoices: {} synced ({} skipped due to missing customer)""".format(
            customers_synced,
            customers_created,
            charges_synced,
            charges_skipped,
            invoices_synced,
            invoices_skipped
        ))
