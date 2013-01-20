from django.contrib import admin

from payments.models import Event, EventProcessingException, Charge


admin.site.register(
    Charge,
    list_display=["stripe_id", "customer", "amount", "description", "paid", "disputed", "refunded", "fee", "receipt_sent", "created_at"],
    search_fields=["stripe_id", "customer__stripe_id", "customer__user__email", "card_last_4", "customer__user__username", "invoice__stripe_id"],
    list_filter=["paid", "disputed", "refunded", "card_kind", "created_at"],
    raw_id_fields=["customer", "invoice"],
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
