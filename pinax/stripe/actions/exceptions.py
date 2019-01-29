import sys
import traceback

from .. import models


def log_exception(data, exception, event=None):
    """
    Log an exception that was captured as a result of processing events

    Args:
        data: the data to log about the exception
        exception: a string describing the exception (can be the exception
            object itself - `str()` gets called on it)
        event: optionally, the event object from which the exception occurred
    """
    info = sys.exc_info()
    info_formatted = "".join(traceback.format_exception(*info)) if info[1] is not None else ""
    models.EventProcessingException.objects.create(
        event=event,
        data=data or "",
        message=str(exception),
        traceback=info_formatted
    )
