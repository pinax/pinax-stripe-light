from django.core.management.base import BaseCommand

from ...actions import plans


class Command(BaseCommand):

    help = "Make sure your Stripe account has the plans"

    def handle(self, *args, **options):
        plans.sync_plans()
