from django.contrib import admin

from payments.models import Event, EventProcessingException, Charge


admin.site.register(
    Charge,
    list_display=["stripe_id", "amount", "description"],
    search_fields=["stripe_id", "customer__stripe_id", "customer__user__email"]
)

admin.site.register(
    EventProcessingException,
    list_display=["message", "event", "created_at"],
    search_fields=["message", "traceback", "data"],
)

admin.site.register(
    Event,
    list_display=["stripe_id", "kind", "livemode", "created_at"],
    search_fields=["stripe_id", "message"],
)
