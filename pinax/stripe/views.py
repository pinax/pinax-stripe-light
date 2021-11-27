from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

import stripe

from .models import Event
from .webhooks import registry


class Webhook(View):

    def add_event(self, data):
        kind = data["type"]
        event = Event.objects.create(
            account_id=data.get("account", ""),
            stripe_id=data["id"],
            kind=kind,
            livemode=data["livemode"],
            message=data,
            api_version=data["api_version"],
            pending_webhooks=data["pending_webhooks"]
        )
        WebhookClass = registry.get(kind)
        if WebhookClass is not None:
            webhook = WebhookClass(event)
            webhook.process()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        signature = self.request.META["HTTP_STRIPE_SIGNATURE"]
        payload = self.request.body
        event = None
        try:
            event = stripe.Webhook.construct_event(payload, signature, settings.PINAX_STRIPE_ENDPOINT_SECRET)
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        if not Event.objects.filter(stripe_id=event.id).exists():
            self.add_event(event.to_dict_recursive())
        return HttpResponse()
