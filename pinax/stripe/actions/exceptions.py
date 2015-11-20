from .. import proxies


def log_exception(data, exception, event=None):
    proxies.EventProcessingExceptionProxy.log(data, exception, event)
