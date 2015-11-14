from django.dispatch import Signal


cancelled = Signal(providing_args=["stripe_response"])
card_changed = Signal(providing_args=["stripe_response"])
subscription_made = Signal(providing_args=["plan", "stripe_response"])
webhook_processing_error = Signal(providing_args=["data", "exception"])

WEBHOOK_SIGNALS = dict([
    (hook, Signal(providing_args=["event"]))
    for hook in [
        "account.application.deauthorized",
        "account.updated",
        "charge.dispute.closed",
        "charge.dispute.created",
        "charge.dispute.updated",
        "charge.failed",
        "charge.refunded",
        "charge.succeeded",
        "coupon.created",
        "coupon.deleted",
        "coupon.updated",
        "customer.created",
        "customer.deleted",
        "customer.discount.created",
        "customer.discount.deleted",
        "customer.discount.updated",
        "customer.subscription.created",
        "customer.subscription.deleted",
        "customer.subscription.trial_will_end",
        "customer.subscription.updated",
        "customer.updated",
        "invoice.created",
        "invoice.payment_failed",
        "invoice.payment_succeeded",
        "invoice.updated",
        "invoiceitem.created",
        "invoiceitem.deleted",
        "invoiceitem.updated",
        "ping",
        "plan.created",
        "plan.deleted",
        "plan.updated",
        "transfer.created",
        "transfer.failed",
        "transfer.updated",
    ]
])
