from django.core.management.base import BaseCommand

from ...actions import syncs


class Command(BaseCommand):

    help = "Make sure your Stripe account has the plans"

    def handle(self, *args, **options):
        syncs.sync_plans()
