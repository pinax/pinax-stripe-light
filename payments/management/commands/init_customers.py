from django.core.management.base import BaseCommand

from ...models import Customer
from ...utils import get_user_model


class Command(BaseCommand):

    help = "Create customer objects for existing users that don't have one"

    def handle(self, *args, **options):
        User = get_user_model()
        for user in User.objects.filter(customer__isnull=True):
            Customer.create(user=user)
            print "Created customer for {0}".format(user.email)
