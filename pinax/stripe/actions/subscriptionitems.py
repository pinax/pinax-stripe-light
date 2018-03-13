import stripe
from django.utils.encoding import smart_str
from .. import models, utils
from ..models import SubscriptionItem


def sync_subscriptionitem_from_stripe_data(subscriptionitem):
    """
    Synchronizes data from the Stripe API for a subscription item

    Args:
        subscriptionitem: data from the Stripe API representing a subscription

    Returns:
        the pinax.stripe.models.Subscription object (created or updated)
    """
    defaults = dict(
        plan=models.Plan.objects.get(stripe_id=subscriptionitem["plan"]["id"]),
        subscription=models.Subscription.objects.get(stripe_id=subscriptionitem["subscription"]),
        metadata=subscriptionitem["metadata"],
        object=subscriptionitem["object"],
        quantity=subscriptionitem["quantity"],
        created_at=utils.convert_tstamp(subscriptionitem["created"]),
    )
    si, created = models.SubscriptionItem.objects.get_or_create(
        stripe_id=subscriptionitem["id"],
        defaults=defaults
    )
    si = utils.update_with_defaults(si, defaults, created)
    return si


def sync_subscription_items(subscription):

    resp = stripe.SubscriptionItem.list(subscription=subscription.stripe_id)
    subscriptionitem_ids = []
    for item in resp.get('data', []):
        subscriptionitem = sync_subscriptionitem_from_stripe_data(item)
        subscriptionitem_ids.append(subscriptionitem.stripe_id)
    SubscriptionItem.objects.exclude(stripe_id__in=subscriptionitem_ids).delete()

    return subscription

def retrieve(subitem_id):

    try:
        subscriptionitem = stripe.SubscriptionItem.retrieve(subitem_id)
    except stripe.InvalidRequestError as e:
        if smart_str(e).find("Invalid subscription_item id") >= 0:
            return
        else:
            raise e

    return subscriptionitem

def create(subscription, plan, metadata=None, prorate=True, proration_date=None, quantity=1):

    subscription_params = dict(
        plan=plan,
        subscription=subscription,
        metadata=metadata,
        prorate=prorate,
        proration_date=proration_date,
        quantity=quantity
    )

    try:
        resp = stripe.SubscriptionItem.create(**subscription_params)
    except stripe.InvalidRequestError as e:
        if smart_str(e).find("add multiple subscription items with the same plan") >= 0:
            resp = retrieve()
        else:
            raise e
    return sync_subscriptionitem_from_stripe_data(resp)


def delete(subitem_id):
    """
        delete an SubscriptionItem

        Args:
            subitem_id: the SubscriptionItem id to delete
        """
    si = retrieve(subitem_id)
    if si:
        si.delete()
        try:
            si = SubscriptionItem.objects.get(sttipe_id=subitem_id)
            si.delete()
        except SubscriptionItem.DoesNotExist:
            pass
