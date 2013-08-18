from django.core.management.base import BaseCommand

from ...utils import get_user_model


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
            print "[{0}/{1} {2}%] Syncing {3} [{4}]".format(
                count, total, perc, user.username, user.pk
            )
            customer = user.customer
            cu = customer.stripe_customer
            customer.sync(cu=cu)
            customer.sync_current_subscription(cu=cu)
            customer.sync_invoices(cu=cu)
            customer.sync_charges(cu=cu)
