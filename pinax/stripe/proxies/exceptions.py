import sys
import traceback

from .. import models


class EventProcessingExceptionProxy(models.EventProcessingException):

    class Meta:
        proxy = True

    @classmethod
    def log(cls, data, exception, event=None):
        info = sys.exc_info()
        info_formatted = "".join(traceback.format_exception(*info)) if info[1] is not None else ""
        cls.objects.create(
            event=event,
            data=data or "",
            message=str(exception),
            traceback=info_formatted
        )
