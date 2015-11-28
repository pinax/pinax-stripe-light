from .. import proxies


def log_exception(data, exception, event=None):
    """
    Log an exception that was captured as a result of processing events

    Args:
        data: the data to log about the exception
        exception: the exception object itself
        event: optionally, the event object from which the exception occurred
    """
    proxies.EventProcessingExceptionProxy.log(data, exception, event)
