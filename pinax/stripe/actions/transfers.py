import stripe

from .. import models, utils


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
    Synchronize a transfer from the Stripe API

    Args:
        transfer: data from Stripe API representing transfer
        event: the event associated with the transfer
    """
    defaults = {
        "amount": utils.convert_amount_for_db(
            transfer["amount"], transfer["currency"]
        ),
        "amount_reversed": utils.convert_amount_for_db(
            transfer["amount_reversed"], transfer["currency"]
        ) if transfer.get("amount_reversed") else None,
        "application_fee": utils.convert_amount_for_db(
            transfer["application_fee"], transfer["currency"]
        ) if transfer.get("application_fee") else None,
        "created": utils.convert_tstamp(transfer["created"]) if transfer.get("created") else None,
        "currency": transfer["currency"],
        "date": utils.convert_tstamp(transfer.get("date")),
        "description": transfer.get("description"),
        "destination": transfer.get("destination"),
        "destination_payment": transfer.get("destination_payment"),
        "event": event,
        "failure_code": transfer.get("failure_code"),
        "failure_message": transfer.get("failure_message"),
        "livemode": transfer.get("livemode"),
        "metadata": dict(transfer.get("metadata", {})),
        "method": transfer.get("method"),
        "reversed": transfer.get("reversed"),
        "source_transaction": transfer.get("source_transaction"),
        "source_type": transfer.get("source_type"),
        "statement_descriptor": transfer.get("statement_descriptor"),
        "status": transfer.get("status"),
        "transfer_group": transfer.get("transfer_group"),
        "type": transfer.get("type")
    }
    obj, created = models.Transfer.objects.update_or_create(
        stripe_id=transfer["id"],
        defaults=defaults
    )
    if not created:
        obj.status = transfer["status"]
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


def create(amount, currency, destination, description, transfer_group=None,
           stripe_account=None, **kwargs):
    """
    Create a transfer.

    Args:
        amount: quantity of money to be sent
        currency: currency for the transfer
        destination: stripe_id of either a connected Stripe Account or Bank Account
        description: an arbitrary string displayed in the webui alongside the transfer
        transfer_group: a string that identifies this transfer as part of a group
        stripe_account: the stripe_id of a Connect account if creating a transfer on
            their behalf
    """
    kwargs.update(dict(
        amount=utils.convert_amount_for_api(amount, currency),
        currency=currency,
        destination=destination,
        description=description
    ))
    if transfer_group:
        kwargs["transfer_group"] = transfer_group
    if stripe_account:
        kwargs["stripe_account"] = stripe_account
    transfer = stripe.Transfer.create(**kwargs)
    return sync_transfer(transfer)
