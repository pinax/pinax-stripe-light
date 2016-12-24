import stripe

from .. import models


def create(country, managed):
    """
    Create an Account.

    Args:
        country: two letter country code for where the individual lives
        managed: boolean field dictating whether we collect details from the user, or Stripe does

    Returns:
        a pinax.stripe.models.Account object
    """
    stripe_account = stripe.Account.create(
        country=country,
        managed=managed
    )
    return sync_account_from_stripe_data(stripe_account)


def sync_account_from_stripe_data(data):
    """
    Create or update using the account object from a Stripe API query.

    Args:
        data: the data representing an account object in the Stripe API

    Returns:
        a pinax.stripe.models.Account object
    """
    obj, created = models.Account.objects.get_or_create(
        stripe_id=data["id"]
    )
    # obj.save()
    return obj
