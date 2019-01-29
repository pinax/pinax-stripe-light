from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from stripe.error import InvalidRequestError

from ...actions import charges, customers, invoices


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
            self.stdout.write(u"[{0}/{1} {2}%] Syncing {3} [{4}]\n".format(
                count, total, perc, username, user.pk
            ))
            customer = customers.get_customer_for_user(user)
            try:
                customers.sync_customer(customer)
            except InvalidRequestError as exc:
                if exc.http_status == 404:  # pragma: no branch
                    # This user doesn't exist (might be in test mode)
                    continue
                raise exc

            if customer.date_purged is None:
                invoices.sync_invoices_for_customer(customer)
                charges.sync_charges_for_customer(customer)
