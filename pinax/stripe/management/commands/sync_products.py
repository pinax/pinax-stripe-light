from django.core.management.base import BaseCommand

from ...actions import products, skus


class Command(BaseCommand):

    help = "Make sure your Stripe account has products"

    def handle(self, *args, **options):
        products.sync_products()
        skus.sync_skus()
