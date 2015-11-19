from .. import proxies


def dupe_event_exists(stripe_id):
    return proxies.EventProxy.objects.filter(stripe_id=stripe_id).exists()


def log_exception(data, exception, event=None):
    proxies.EventProcessingExceptionProxy.log(data, exception, event)


def add_event(stripe_id, kind, livemode, message, api_version="", request_id="", pending_webhooks=0):
    event = proxies.EventProxy.objects.create(
        stripe_id=stripe_id,
        kind=kind,
        livemode=livemode,
        webhook_message=message,
        api_version=api_version,
        request=request_id,
        pending_webhooks=pending_webhooks
    )
    event.validate()
    event.process()
