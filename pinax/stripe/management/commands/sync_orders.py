from django.core.management.base import BaseCommand

from ...actions import orders


class Command(BaseCommand):

    help = "Sync up your local orders with stripe"

    def handle(self, *args, **options):
        orders.sync_orders()
