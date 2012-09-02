from django.core.management.base import BaseCommand

from django.contrib.auth.models import User

from payments.models import Customer
from payments.settings import TRIAL_PERIOD_FOR_USER_CALLBACK
from payments.settings import DEFAULT_PLAN


class Command(BaseCommand):
    
    help = "Create customer objects for existing users that don't have one"
    
    def handle(self, *args, **options):
        for user in User.objects.filter(customer__isnull=True):
            trial_days = None
            if TRIAL_PERIOD_FOR_USER_CALLBACK:
                trial_days = TRIAL_PERIOD_FOR_USER_CALLBACK(user)
            cus = Customer.create(user=user)
            if DEFAULT_PLAN and trial_days:
                cus.purchase(plan=DEFAULT_PLAN, trial_days=trial_days)
            print "Created customer for %s" % user.email
