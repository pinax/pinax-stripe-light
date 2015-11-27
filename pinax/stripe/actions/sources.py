from .. import proxies
from .. import utils


def create_card(customer, token):
    source = customer.stripe_customer.sources.create(source=token)
    sync_payment_source_from_stripe_data(customer, source)


def update_card(customer, source, name=None, exp_month=None, exp_year=None):
    stripe_source = customer.stripe_customer.sources.retrieve(source)
    if name is not None:
        stripe_source.name = name
    if exp_month is not None:
        stripe_source.exp_month = exp_month
    if exp_year is not None:
        stripe_source.exp_year = exp_year
    s = stripe_source.save()
    sync_payment_source_from_stripe_data(customer, s)


def delete_card(customer, source):
    customer.stripe_customer.sources.retrieve(source).delete()
    delete_card_object(source)


def delete_card_object(source):
    if source.startswith("card_"):
        proxies.CardProxy.objects.filter(stripe_id=source).delete()


def sync_card(customer, source):
    defaults = dict(
        customer=customer,
        name=source["name"] or "",
        address_line_1=source["address_line1"] or "",
        address_line_1_check=source["address_line1_check"] or "",
        address_line_2=source["address_line2"] or "",
        address_city=source["address_city"] or "",
        address_state=source["address_state"] or "",
        address_country=source["address_country"] or "",
        address_zip=source["address_zip"] or "",
        address_zip_check=source["address_zip_check"] or "",
        brand=source["brand"],
        country=source["country"],
        cvc_check=source["cvc_check"],
        dynamic_last4=source["dynamic_last4"] or "",
        exp_month=source["exp_month"],
        exp_year=source["exp_year"],
        funding=source["funding"] or "",
        last4=source["last4"] or "",
        fingerprint=source["fingerprint"] or ""
    )
    card, created = proxies.CardProxy.objects.get_or_create(
        stripe_id=source["id"],
        defaults=defaults
    )
    utils.update_with_defaults(card, defaults, created)


def sync_bitcoin(customer, source):
    defaults = dict(
        customer=customer,
        active=source["active"],
        amount=utils.convert_amount_for_db(source["amount"], source["currency"]),
        amount_received=utils.convert_amount_for_db(source["amount_received"], source["currency"]),
        bitcoin_amount=source["bitcoin_amount"],
        bitcoin_amount_received=source["bitcoin_amount_received"],
        bitcoin_uri=source["bitcoin_uri"],
        currency=source["currency"],
        description=source["description"],
        email=source["email"],
        filled=source["filled"],
        inbound_address=source["inbound_address"],
        payment=source["payment"] if "payment" in source else "",
        refund_address=source["refund_address"] or "",
        uncaptured_funds=source["uncaptured_funds"],
        used_for_payment=source["used_for_payment"]
    )
    receiver, created = proxies.BitcoinRecieverProxy.objects.get_or_create(
        stripe_id=source["id"],
        defaults=defaults
    )
    utils.update_with_defaults(receiver, defaults, created)


def sync_payment_source_from_stripe_data(customer, source):
    if source["id"].startswith("card_"):
        sync_card(customer, source)
    else:
        sync_bitcoin(customer, source)
