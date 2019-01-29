from django.core.management.base import BaseCommand

from ...actions import coupons


class Command(BaseCommand):

    help = "Make sure your Stripe account has the coupons"

    def handle(self, *args, **options):
        coupons.sync_coupons()
