from django.core.urlresolvers import resolve
from django.shortcuts import redirect

from .actions import customers, subscriptions
from .conf import settings


class ActiveSubscriptionMiddleware(object):

    def process_request(self, request):
        if request.user.is_authenticated() and not request.user.is_staff:
            url_name = resolve(request.path).url_name
            if url_name not in settings.PINAX_STRIPE_SUBSCRIPTION_REQUIRED_EXCEPTION_URLS:
                customer = customers.get_customer_for_user(request.user)
                if not subscriptions.has_active_subscription(customer):
                    return redirect(
                        settings.PINAX_STRIPE_SUBSCRIPTION_REQUIRED_REDIRECT
                    )
