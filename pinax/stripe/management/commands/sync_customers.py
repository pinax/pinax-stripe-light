from django.core.management.base import BaseCommand

from django.contrib.auth import get_user_model

from ...actions import customers, charges, invoices


class Command(BaseCommand):

    help = "Sync customer data"

    def handle(self, *args, **options):
        User = get_user_model()
        qs = User.objects.exclude(customer__isnull=True)
        count = 0
        total = qs.count()
        for user in qs:
            count += 1
            perc = int(round(100 * (float(count) / float(total))))
            username = getattr(user, user.USERNAME_FIELD)
            print("[{0}/{1} {2}%] Syncing {3} [{4}]".format(
                count, total, perc, username, user.pk
            ))
            customer = customers.get_customer_for_user(user)
            customers.sync_customer(customer)
            invoices.sync_invoices_for_customer(customer)
            charges.sync_charges_for_customer(customer)
