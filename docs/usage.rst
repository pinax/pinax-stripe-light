.. _usage:

Usage
=====

What you do with payments and subscriptions is a highly custom thing so it is pretty
hard to write a generic integration guide, but one typical thing you might want to do
is disable access to most of the site if the subscription fails being active. You can
accomplish this with the following middleware::

    from django.conf import settings
    from django.core.urlresolvers import reverse
    from django.shortcuts import redirect
    
    URLS = [reverse(url) for url in settings.SUBSCRIPTION_REQUIRED_EXCEPTION_URLS]
    
    
    class ActiveSubscriptionMiddleware(object):
        
        def process_request(self, request):
            if request.user.is_authenticated() and not request.user.is_staff:
                if request.path not in URLS:
                    if not request.user.customer.has_active_subscription():
                        return redirect(settings.SUBSCRIPTION_REQUIRED_REDIRECT)

The two ``SUBSCRIPTION_REQUIRED_EXCEPTION_URLS`` is a list of url names that the user can
no matter what and the ``SUBSCRIPTION_REQUIRED_REDIRECT`` is the url to redirect them to if
they hit a pay-only page.

Of course, your site might function more on levels and limits rather than lockout. It's up
to use to write the necessary code to interpret how your site should behave, however, you
can rely on ``request.user.customer`` giving you an object with relevant information to
make that decision such as ``customer.plan`` and ``customer.has_active_subscription``.
