from . import syncs
from .. import proxies


def create_card(customer, token):
    source = customer.stripe_customer.sources.create(source=token)
    syncs.sync_payment_source_from_stripe_data(customer, source)


def update_card(customer, source, name=None, exp_month=None, exp_year=None):
    stripe_source = customer.stripe_customer.sources.retrieve(source)
    if name is not None:
        stripe_source.name = name
    if exp_month is not None:
        stripe_source.exp_month = exp_month
    if exp_year is not None:
        stripe_source.exp_year = exp_year
    s = stripe_source.save()
    syncs.sync_payment_source_from_stripe_data(customer, s)


def delete_card(customer, source):
    customer.stripe_customer.sources.retrieve(source).delete()
    delete_card_object(source)
    syncs.sync_customer(customer)


def delete_card_object(source):
    if source.startswith("card_"):
        proxies.CardProxy.objects.filter(stripe_id=source).delete()
