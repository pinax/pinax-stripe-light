from django.core.management.base import BaseCommand

from django.contrib.auth import get_user_model

from payments.models import Customer

User = get_user_model()


class Command(BaseCommand):
    
    help = "Create customer objects for existing users that don't have one"
    
    def handle(self, *args, **options):
        for user in User.objects.filter(customer__isnull=True):
            Customer.create(user=user)
            print "Created customer for %s" % user.email
