from __future__ import unicode_literals

from django.core.management.base import BaseCommand
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User

from payments.models import Customer


class Command(BaseCommand):
    
    help = "Create customer objects for existing users that don't have one"
    
    def handle(self, *args, **options):
        for user in User.objects.filter(customer__isnull=True):
            Customer.create(user=user)
            print "Created customer for {0}".format(user.email)
