from .. import models, utils


def create_card(customer, token):
    """
    Creates a new card for a customer

    Args:
        customer: the customer to create the card for
        token: the token created from Stripe.js
    """
    source = customer.stripe_customer.sources.create(source=token)
    return sync_payment_source_from_stripe_data(customer, source)


def delete_card(customer, source):
    """
    Deletes a card from a customer

    Args:
        customer: the customer to delete the card from
        source: the Stripe ID of the payment source to delete
    """
    customer.stripe_customer.sources.retrieve(source).delete()
    return delete_card_object(source)


def delete_card_object(source):
    """
    Deletes the local card object (Card)

    Args:
        source: the Stripe ID of the card
    """
    if source.startswith("card_"):
        return models.Card.objects.filter(stripe_id=source).delete()


def sync_card(customer, source):
    """
    Synchronizes the data for a card locally for a given customer

    Args:
        customer: the customer to create or update a card for
        source: data representing the card from the Stripe API
    """
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
        country=source["country"] or "",
        cvc_check=source["cvc_check"] or "",
        dynamic_last4=source["dynamic_last4"] or "",
        exp_month=source["exp_month"],
        exp_year=source["exp_year"],
        funding=source["funding"] or "",
        last4=source["last4"] or "",
        fingerprint=source["fingerprint"] or ""
    )
    card, created = models.Card.objects.get_or_create(
        stripe_id=source["id"],
        defaults=defaults
    )
    return utils.update_with_defaults(card, defaults, created)


def sync_bitcoin(customer, source):
    """
    Synchronizes the data for a Bitcoin receiver locally for a given customer

    Args:
        customer: the customer to create or update a Bitcoin receiver for
        source: data reprenting the Bitcoin receiver from the Stripe API
    """
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
    receiver, created = models.BitcoinReceiver.objects.get_or_create(
        stripe_id=source["id"],
        defaults=defaults
    )
    return utils.update_with_defaults(receiver, defaults, created)


def sync_payment_source_from_stripe_data(customer, source):
    """
    Synchronizes the data for a payment source locally for a given customer

    Args:
        customer: the customer to create or update a Bitcoin receiver for
        source: data reprenting the payment source from the Stripe API
    """
    if source["object"] == "card":
        return sync_card(customer, source)
    # NOTE: this does not seem to be a thing anymore?!
    if source["object"] == "bitcoin_receiver":
        return sync_bitcoin(customer, source)


def update_card(customer, source, name=None, exp_month=None, exp_year=None):
    """
    Updates a card for a given customer

    Args:
        customer: the customer for whom to update the card
        source: the Stripe ID of the card to update
        name: optionally, a name to give the card
        exp_month: optionally, the expiration month for the card
        exp_year: optionally, the expiration year for the card
    """
    stripe_source = customer.stripe_customer.sources.retrieve(source)
    if name is not None:
        stripe_source.name = name
    if exp_month is not None:
        stripe_source.exp_month = exp_month
    if exp_year is not None:
        stripe_source.exp_year = exp_year
    s = stripe_source.save()
    return sync_payment_source_from_stripe_data(customer, s)
