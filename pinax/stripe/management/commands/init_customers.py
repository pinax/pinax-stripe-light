from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ...actions import customers


class Command(BaseCommand):

    help = "Create customer objects for existing users that do not have one"

    def handle(self, *args, **options):
        User = get_user_model()
        for user in User.objects.filter(customer__isnull=True):
            customers.create(user=user, charge_immediately=False)
            self.stdout.write("Created customer for {0}\n".format(user.email))
