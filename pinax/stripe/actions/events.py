from .. import proxies


def dupe_event_exists(stripe_id):
    return proxies.EventProxy.dupe_exists(stripe_id)


def log_exception(data, exception, event=None):
    proxies.EventProcessingExceptionProxy.log(data, exception, event)


def add_event(stripe_id, kind, livemode, message):
    proxies.EventProxy.add_event(
        stripe_id=stripe_id,
        kind=kind,
        livemode=livemode,
        message=message
    )
