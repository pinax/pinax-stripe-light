from django.contrib import admin

from payments.models import Event, EventProcessingException, Transfer, Charge, Invoice, InvoiceItem, CurrentSubscription, Customer


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
    raw_id_fields=["customer"],
    list_display=["stripe_id", "kind", "livemode", "valid", "processed", "created_at"],
    list_filter=["kind", "created_at", "valid", "processed"],
    search_fields=["stripe_id", "customer__stripe_id", "customer__user__username", "customer__user__email", "validated_message"],
)


class CurrentSubscriptionInline(admin.TabularInline):
    model = CurrentSubscription


admin.site.register(
    Customer,
    raw_id_fields=["user"],
    list_display=["stripe_id", "user", "card_kind", "card_last_4"],
    search_fields=["stripe_id", "user__username", "user__email"],
    inlines=[CurrentSubscriptionInline]
)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem


admin.site.register(
    Invoice,
    raw_id_fields=["customer"],
    list_display=["stripe_id", "paid", "period_start", "period_end", "subtotal", "total"],
    search_fields=["stripe_id", "customer__stripe_id", "customer__user__username", "customer__user__email"],
    inlines=[InvoiceItemInline]
)


admin.site.register(
    Transfer,
    raw_id_fields=["event"],
    list_display=["stripe_id", "amount", "status", "date", "description"],
    search_fields=["stripe_id", "event__stripe_id"]
)
