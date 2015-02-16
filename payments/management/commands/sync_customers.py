from django.core.management.base import BaseCommand

from ...utils import get_ref_model


class Command(BaseCommand):

    help = "Sync customer data"

    def handle(self, *args, **options):
        Ref = get_ref_model()
        qs = Ref.objects.exclude(customer__isnull=True)
        count = 0
        total = qs.count()
        for ref in qs:
            count += 1
            perc = int(round(100 * (float(count) / float(total))))
            print("[{0}/{1} {2}%] Syncing {3}]".format(
                count, total, perc, ref
            ))
            customer = ref.customer
            cu = customer.stripe_customer
            customer.sync(cu=cu)
            customer.sync_current_subscription(cu=cu)
            customer.sync_invoices(cu=cu)
            customer.sync_charges(cu=cu)
