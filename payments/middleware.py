from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from .models import Customer


URLS = [reverse(url) for url in settings.SUBSCRIPTION_REQUIRED_EXCEPTION_URLS]


class ActiveSubscriptionMiddleware(object):

    def process_request(self, request):
        if request.user.is_authenticated() and not request.user.is_staff:
            if request.path not in URLS:
                try:
                    if not request.user.customer.has_active_subscription():
                        return redirect(settings.SUBSCRIPTION_REQUIRED_REDIRECT)
                except Customer.DoesNotExist:
                    return redirect(settings.SUBSCRIPTION_REQUIRED_REDIRECT)
