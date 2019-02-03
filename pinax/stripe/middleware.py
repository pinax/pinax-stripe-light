import django
from django.shortcuts import redirect

from .actions import customers, subscriptions
from .conf import settings

try:
    from django.urls import resolve
except ImportError:
    from django.core.urlresolvers import resolve

try:
    from django.utils.deprecation import MiddlewareMixin as MixinorObject
except ImportError:
    MixinorObject = object


class ActiveSubscriptionMiddleware(MixinorObject):

    def process_request(self, request):
        is_authenticated = request.user.is_authenticated
        if django.VERSION < (1, 10):
            is_authenticated = is_authenticated()

        if is_authenticated and not request.user.is_staff:
            url_name = resolve(request.path).url_name
            if url_name not in settings.PINAX_STRIPE_SUBSCRIPTION_REQUIRED_EXCEPTION_URLS:
                customer = customers.get_customer_for_user(request.user)
                if not subscriptions.has_active_subscription(customer):
                    return redirect(
                        settings.PINAX_STRIPE_SUBSCRIPTION_REQUIRED_REDIRECT
                    )
