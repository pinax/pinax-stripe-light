.. _signals:

Signals
=======

There are a handful of application level signals as well as a 1:1
signal for webhook that Stripe sends to allow you to respond to whatever
activity Stripe sends as a webhook.

cancelled
---------

:providing_args: `stripe_response`


card_changed
------------

:providing_args: `stripe_response`


subscription_made
-----------------

:providing_args: `plan`, `stripe_response`


webhook_processing_error
------------------------

:providing_args: `data`, `exception`


WEBHOOK_SIGNALS
---------------

This is a dictionary, indexed by the names for each webhook event. The
signal object found as the value for each item in the dictionary provides
an `event` argument the the instance of `payments.models.Event` that has
all the data related to the event.
