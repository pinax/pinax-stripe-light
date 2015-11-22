import traceback

from .. import models


class EventProcessingExceptionProxy(models.EventProcessingException):

    class Meta:
        proxy = True

    @classmethod
    def log(cls, data, exception, event=None):
        cls.objects.create(
            event=event,
            data=data or "",
            message=str(exception),
            traceback=traceback.format_exc() if isinstance(exception, Exception) else ""
        )
