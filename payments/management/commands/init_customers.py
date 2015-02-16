from django.core.management.base import BaseCommand

from ...models import Customer
from ...utils import get_ref_model


class Command(BaseCommand):

    help = "Create customer objects for existing users that don't have one"

    def handle(self, *args, **options):
        Ref = get_ref_model()
        for ref in Ref.objects.filter(customer__isnull=True):
            Customer.create(ref=ref)
            print("Created customer for {0}".format(ref))
