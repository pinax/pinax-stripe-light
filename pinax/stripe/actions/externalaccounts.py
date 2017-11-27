from .. import models


def create_bank_account(account, account_number, country, currency, **kwargs):
    """
    Create a Bank Account.

    Args:
        account: the stripe.Account object we're attaching
                 the bank account to
        account_number: the Bank Account number
        country: two letter country code
        currency: three letter currency code

        There are additional properties that can be set, please see:
        https://stripe.com/docs/api#account_create_bank_account

    Returns:
        a pinax.stripe.models.BankAccount object
    """
    external_account = account.external_accounts.create(
        external_account=dict(
            object="bank_account",
            account_number=account_number,
            country=country,
            currency=currency,
            **kwargs
        )
    )
    return sync_bank_account_from_stripe_data(
        external_account
    )


def sync_bank_account_from_stripe_data(data):
    """
    Create or update using the account object from a Stripe API query.

    Args:
        data: the data representing an account object in the Stripe API

    Returns:
        a pinax.stripe.models.Account object
    """
    account = models.Account.objects.get(
        stripe_id=data["account"]
    )
    kwargs = {
        "stripe_id": data["id"],
        "account": account
    }
    obj, created = models.BankAccount.objects.get_or_create(
        **kwargs
    )
    top_level_attrs = (
        "account_holder_name", "account_holder_type",
        "bank_name", "country", "currency", "default_for_currency",
        "fingerprint", "last4", "metadata", "routing_number",
        "status"
    )
    for a in top_level_attrs:
        setattr(obj, a, data.get(a))
    obj.save()
    return obj
