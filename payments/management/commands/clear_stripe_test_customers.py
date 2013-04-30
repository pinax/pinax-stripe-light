from django.conf import settings
from django.core.management.base import BaseCommand

import stripe

class Command(BaseCommand):
    help = "Clear all test mode customers from your stripe account."
    __test__ = False

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', 1))
        stripe.api_key = settings.STRIPE_SECRET_KEY
        customer_chunk=[0]
        if verbosity > 0:
            print "Clearing stripe test customers:"
        
        num_checked = 0
        while len(customer_chunk) is not 0:
            customer_chunk = stripe.Customer.all().data

            if verbosity > 1:     
                print "Processing records %s-%s" % (num_checked, num_checked+len(customer_chunk))

            for c in customer_chunk:
                if verbosity > 2:
                    print "Deleting %s..." % (c.description),

                if not c.livemode:
                    c.delete()

                    if verbosity > 2:
                        print "done"
            
            num_checked = num_checked + len(customer_chunk)
        
        if verbosity > 0:
            print "Finished clearing stripe test customers."
