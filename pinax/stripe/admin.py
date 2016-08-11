from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from .models import (  # @@@ make all these read-only
    Charge,
    Subscription,
    Customer,
    Event,
    EventProcessingException,
    Invoice,
    InvoiceItem,
    Plan,
    Transfer
)


def user_search_fields():  # coverage: omit
    User = get_user_model()
    fields = [
        "user__{0}".format(User.USERNAME_FIELD)
    ]
    if "email" in [f.name for f in User._meta.fields]:
        fields += ["user__email"]
    return fields


def customer_search_fields():
    return [
        "customer__{0}".format(field)
        for field in user_search_fields()
    ]


class CustomerHasCardListFilter(admin.SimpleListFilter):
    title = "card presence"
    parameter_name = "has_card"

    def lookups(self, request, model_admin):
        return [
            ["yes", "Has Card"],
            ["no", "Does Not Have a Card"]
        ]

    def queryset(self, request, queryset):
        no_card = Q(card__fingerprint="") | Q(card=None)
        if self.value() == "yes":
            return queryset.exclude(no_card)
        elif self.value() == "no":
            return queryset.filter(no_card)
        return queryset.all()


class InvoiceCustomerHasCardListFilter(admin.SimpleListFilter):
    title = "card presence"
    parameter_name = "has_card"

    def lookups(self, request, model_admin):
        return [
            ["yes", "Has Card"],
            ["no", "Does Not Have a Card"]
        ]

    def queryset(self, request, queryset):
        no_card = (Q(customer__card__fingerprint="") | Q(customer__card=None))
        if self.value() == "yes":  # coverage: omit
            # Worked when manually tested, getting a weird error otherwise
            # Better than no tests at all
            return queryset.exclude(no_card)
        elif self.value() == "no":
            return queryset.filter(no_card)
        return queryset.all()


class CustomerSubscriptionStatusListFilter(admin.SimpleListFilter):
    title = "subscription status"
    parameter_name = "sub_status"

    def lookups(self, request, model_admin):
        statuses = [
            [x, x.replace("_", " ").title()]
            for x in Subscription.objects.all().values_list(
                "status",
                flat=True
            ).distinct()
        ]
        statuses.append(["none", "No Subscription"])
        return statuses

    def queryset(self, request, queryset):
        if self.value() == "none":
            # Get customers with 0 subscriptions
            return queryset.annotate(subs=Count('subscription')).filter(subs=0)
        elif self.value():
            # Get customer pks without a subscription with this status
            customers = Subscription.objects.filter(
                status=self.value()).values_list(
                'customer', flat=True).distinct()
            # Filter by those customers
            return queryset.filter(pk__in=customers)
        return queryset.all()


admin.site.register(
    Charge,
    list_display=[
        "stripe_id",
        "customer",
        "amount",
        "description",
        "paid",
        "disputed",
        "refunded",
        "receipt_sent",
        "created_at"
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id",
        "invoice__stripe_id"
    ] + customer_search_fields(),
    list_filter=[
        "paid",
        "disputed",
        "refunded",
        "created_at"
    ],
    raw_id_fields=[
        "customer",
        "invoice"
    ],
)

admin.site.register(
    EventProcessingException,
    list_display=[
        "message",
        "event",
        "created_at"
    ],
    search_fields=[
        "message",
        "traceback",
        "data"
    ],
    raw_id_fields=[
        "event"
    ],
)

admin.site.register(
    Event,
    raw_id_fields=["customer"],
    list_display=[
        "stripe_id",
        "kind",
        "livemode",
        "valid",
        "processed",
        "created_at"
    ],
    list_filter=[
        "kind",
        "created_at",
        "valid",
        "processed"
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id",
        "validated_message"
    ] + customer_search_fields(),
)


class SubscriptionInline(admin.TabularInline):
    model = Subscription


def subscription_status(obj):
    return ", ".join([subscription.status for subscription in obj.subscription_set.all()])
subscription_status.short_description = "Subscription Status"


admin.site.register(
    Customer,
    raw_id_fields=["user"],
    list_display=[
        "stripe_id",
        "user",
        "account_balance",
        "currency",
        "delinquent",
        "default_source",
        subscription_status,
        "date_purged"
    ],
    list_filter=[
        "delinquent",
        CustomerHasCardListFilter,
        CustomerSubscriptionStatusListFilter
    ],
    search_fields=[
        "stripe_id",
    ] + user_search_fields(),
    inlines=[SubscriptionInline]
)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem


def customer_has_card(obj):
    return obj.customer.card_set.exclude(fingerprint='').exists()
customer_has_card.short_description = "Customer Has Card"


def customer_user(obj):
    User = get_user_model()
    username = getattr(obj.customer.user, User.USERNAME_FIELD)
    email = getattr(obj, "email", "")
    return "{0} <{1}>".format(
        username,
        email
    )
customer_user.short_description = "Customer"


admin.site.register(
    Invoice,
    raw_id_fields=["customer"],
    list_display=[
        "stripe_id",
        "paid",
        "closed",
        customer_user,
        customer_has_card,
        "period_start",
        "period_end",
        "subtotal",
        "total"
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id",
    ] + customer_search_fields(),
    list_filter=[
        InvoiceCustomerHasCardListFilter,
        "paid",
        "closed",
        "attempted",
        "attempt_count",
        "created_at",
        "date",
        "period_end",
        "total"
    ],
    inlines=[InvoiceItemInline]
)

admin.site.register(
    Plan,
    list_display=[
        "stripe_id",
        "name",
        "amount",
        "currency",
        "interval",
        "interval_count",
        "trial_period_days",
    ],
    search_fields=[
        "stripe_id",
        "name",
    ],
    list_filter=[
        "currency",
    ],
    readonly_fields=[
        "stripe_id",
        "name",
        "amount",
        "currency",
        "interval",
        "interval_count",
        "trial_period_days",
        "statement_descriptor",
        "created_at",
    ],
)

admin.site.register(
    Transfer,
    raw_id_fields=["event"],
    list_display=[
        "stripe_id",
        "amount",
        "status",
        "date",
        "description"
    ],
    search_fields=[
        "stripe_id",
        "event__stripe_id"
    ]
)
