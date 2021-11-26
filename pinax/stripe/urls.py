from django.urls import path

from .views import (
    InvoiceListView,
    PaymentMethodCreateView,
    PaymentMethodDeleteView,
    PaymentMethodListView,
    PaymentMethodUpdateView,
    SubscriptionCreateView,
    SubscriptionDeleteView,
    SubscriptionListView,
    SubscriptionUpdateView,
    Webhook
)

urlpatterns = [
    path("subscriptions/", SubscriptionListView.as_view(), name="pinax_stripe_subscription_list"),
    path("subscriptions/create/", SubscriptionCreateView.as_view(), name="pinax_stripe_subscription_create"),
    path("subscriptions/<int:pk>/delete/", SubscriptionDeleteView.as_view(), name="pinax_stripe_subscription_delete"),
    path("subscriptions/<int:pk>/update/", SubscriptionUpdateView.as_view(), name="pinax_stripe_subscription_update"),

    path("payment-methods/", PaymentMethodListView.as_view(), name="pinax_stripe_payment_method_list"),
    path("payment-methods/create/", PaymentMethodCreateView.as_view(), name="pinax_stripe_payment_method_create"),
    path("payment-methods/<int:pk>/delete/", PaymentMethodDeleteView.as_view(), name="pinax_stripe_payment_method_delete"),
    path("payment-methods/<int:pk>/update/", PaymentMethodUpdateView.as_view(), name="pinax_stripe_payment_method_update"),

    path("invoices/", InvoiceListView.as_view(), name="pinax_stripe_invoice_list"),

    path("webhook/", Webhook.as_view(), name="pinax_stripe_webhook"),
]
