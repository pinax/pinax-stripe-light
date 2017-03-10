import stripe

from .. import models
from .. import utils


def during(year, month):
    """
    Return a queryset of pinax.stripe.models.Transfer objects for the provided
    year and month.

    Args:
        year: 4-digit year
        month: month as a integer, 1=January through 12=December
    """
    return models.Transfer.objects.filter(
        date__year=year,
        date__month=month
    )


def sync_transfer(transfer, event=None):
    """
    Syncronize a transfer from the Stripe API

    Args:
        transfer: data from Stripe API representing transfer
        event: the event associated with the transfer
    """
    defaults = {
        "amount": utils.convert_amount_for_db(
            transfer['amount'], transfer['currency']
        ),
        "amount_reversed": utils.convert_amount_for_db(
            transfer['amount_reversed'], transfer['currency']
        ) if transfer['amount_reversed'] else None,
        "application_fee": utils.convert_amount_for_db(
            transfer['application_fee'], transfer['currency']
        ) if transfer['application_fee'] else None,
        "created": utils.convert_tstamp(transfer['created']),
        "currency": transfer['currency'],
        "date": utils.convert_tstamp(transfer.get('date')),
        "description": transfer['description'],
        "destination": transfer['destination'],
        "destination_payment": transfer.get('destination_payment'),
        "event": event,
        "failure_code": transfer['failure_code'],
        "failure_message": transfer['failure_message'],
        "livemode": transfer['livemode'],
        "metadata": dict(transfer['metadata']),
        "method": transfer['method'],
        "reversed": transfer['reversed'],
        "source_transaction": transfer['source_transaction'],
        "source_type": transfer['source_type'],
        "statement_descriptor": transfer['statement_descriptor'],
        "status": transfer['status'],
        "transfer_group": transfer['transfer_group'],
        "type": transfer['type']
    }
    obj, created = models.Transfer.objects.update_or_create(
        stripe_id=transfer['id'],
        defaults=defaults
    )
    if not created:
        obj.status = transfer['status']
        obj.save()
    return obj


def update_status(transfer):
    """
    Update the status of a pinax.stripe.models.Transfer object from Stripe API

    Args:
        transfer: a pinax.stripe.models.Transfer object to update
    """
    transfer.status = stripe.Transfer.retrieve(transfer.stripe_id).status
    transfer.save()


def create(
    amount, currency, destination, description,
    transfer_group=None, stripe_account=None, **kwargs
):
    """
    Create a transfer.

    Args:
        amount: quantity of money to be sent
        currency: currency for the transfer
        destination: stripe_id of either a connected Stripe Account or Bank Account
        description: an arbitrary string displayed in the webui alongside the transfer
        transfer_group: a string that identifies this transfer as part of a group
        stripe_account: the stripe_id of a connect account if creating a transfer on
            their behalf
    """
    kwargs.update(dict(
        amount=utils.convert_amount_for_api(amount, currency),
        currency=currency,
        destination=destination,
        description=description
    ))
    if transfer_group:
        kwargs['transfer_group'] = stripe_account
    if stripe_account:
        kwargs['stripe_account'] = stripe_account
    transfer = stripe.Transfer.create(**kwargs)
    return sync_transfer(transfer)
