import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

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
            webhook_message=data,
            api_version=data["api_version"],
            pending_webhooks=data["pending_webhooks"]
        )
        WebhookClass = registry.get(kind)
        if WebhookClass is not None:
            webhook = WebhookClass(event)
            webhook.process()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(Webhook, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = json.loads(smart_str(self.request.body))
        if not Event.objects.filter(stripe_id=data["id"]).exists():
            self.add_event(data)
        return HttpResponse()
