# Signals

There is a signal sent for every [webhook event](webhooks.md#events).  You can
access them by doing the following:

```python
# receivers.py
from django.dispatch import receiver

from pinax.stripe.signals import WEBHOOK_SIGNALS


@receiver(WEBHOOK_SIGNALS["invoice.payment_succeeded"])
def handle_payment_succeeded(sender, event, **kwargs):
    pass  # do what it is you want to do here
```

If you make sure that `receivers.py` is [imported at startup](https://github.com/pinax/pinax-starter-projects/blob/account/project_name/apps.py#L11)
then this code example above will execute the `handle_payment_succeeded` function
everytime the `invoice.payment_succeeded` event is sent by Stripe and processed by your
webhook endpoint.

The `event` object is a processed and verified [Event model instance](https://github.com/pinax/pinax-stripe/blob/master/pinax/stripe/models.py#L55)
which gives you access to all the raw data of the event.
