from .. import models
from ..webhooks import registry


def add_event(stripe_id, kind, livemode, message, api_version="", request_id="", pending_webhooks=0):
    """
    Adds and processes an event from a received webhook

    Args:
        stripe_id: the stripe id of the event
        kind: the label of the event
        livemode: True or False if the webhook was sent from livemode or not
        message: the data of the webhook
        api_version: the version of the Stripe API used
        request_id: the id of the request that initiated the webhook
        pending_webhooks: the number of pending webhooks
    """
    event = models.Event.objects.create(
        stripe_id=stripe_id,
        kind=kind,
        livemode=livemode,
        webhook_message=message,
        api_version=api_version,
        request=request_id,
        pending_webhooks=pending_webhooks
    )
    WebhookClass = registry.get(kind)
    if WebhookClass is not None:
        webhook = WebhookClass(event)
        webhook.process()


def dupe_event_exists(stripe_id):
    """
    Checks if a duplicate event exists

    Args:
        stripe_id: the Stripe ID of the event to Checks

    Returns:
        True, if the event already exists, otherwise, False
    """
    return models.Event.objects.filter(stripe_id=stripe_id).exists()
