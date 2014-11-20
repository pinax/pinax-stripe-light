.. _usage:

Usage
=====

What you do with payments and subscriptions is a highly custom thing so it is pretty
hard to write a generic integration guide, but one typical thing you might want to do
is disable access to most of the site if the subscription fails being active. You can
accomplish this by adding the `payments.middleware.ActiveSubscriptionMiddleware`
to your `settings.py`::

    MIDDLEWARE_CLASSES = [
        ...
        "payments.middleware.ActiveSubscriptionMiddleware",
        ...
    ]

There are two settings you'll need to define for this middleware to work. The first,
``SUBSCRIPTION_REQUIRED_EXCEPTION_URLS`` is a list of url names that the user can
access no matter what, and the second one, ``SUBSCRIPTION_REQUIRED_REDIRECT`` is the url
to redirect them to if they hit a pay-only page.

Of course, your site might function more on levels and limits rather than lockout. It's up
to you to write the necessary code to interpret how your site should behave, however, you
can rely on ``request.user.customer`` giving you an object with relevant information to
make that decision such as ``customer.plan`` and ``customer.has_active_subscription``.
