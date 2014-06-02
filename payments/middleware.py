from django.conf import settings
from django.core.urlresolvers import resolve
from django.shortcuts import redirect

from .models import Customer


class ActiveSubscriptionMiddleware(object):

    def process_request(self, request):
        if request.user.is_authenticated() and not request.user.is_staff:
            url_name = resolve(request.path).url_name
            if url_name not in settings.SUBSCRIPTION_REQUIRED_EXCEPTION_URLS:
                try:
                    if not request.user.customer.has_active_subscription():
                        return redirect(
                            settings.SUBSCRIPTION_REQUIRED_REDIRECT
                        )
                except Customer.DoesNotExist:
                    return redirect(settings.SUBSCRIPTION_REQUIRED_REDIRECT)
