from django.conf.urls.defaults import patterns, url

from django.views.generic.simple import direct_to_template

from payments.forms import PlanForm


urlpatterns = patterns(
    "payments.views",
    url(r"^webhook/$", "webhook", name="payments_webhook"),
    
    url(r"^a/subscribe/$", "subscribe", name="payments_ajax_subscribe"),
    url(r"^a/change/card/$", "change_card", name="payments_ajax_change_card"),
    url(r"^a/change/plan/$", "change_plan", name="payments_ajax_change_plan"),
    url(r"^a/cancel/$", "cancel", name="payments_ajax_cancel"),
    
    url(
        r"^subscribe/$",
        direct_to_template,
        {
            "template": "payments/subscribe.html",
            "extra_context": {"form": PlanForm}
        },
        name="payments_subscribe"
    ),
    url(
        r"^change/card/$",
        direct_to_template,
        {"template": "payments/change_card.html"},
        name="payments_change_card"
    ),
    url(
        r"^change/plan/$",
        direct_to_template,
        {
            "template": "payments/change_plan.html",
            "extra_context": {"form": PlanForm}
        },
        name="payments_change_plan"
    ),
    url(
        r"^cancel/$",
        direct_to_template,
        {"template": "payments/cancel.html"},
        name="payments_cancel"
    ),
    url(
        r"^history/$",
        direct_to_template,
        {"template": "payments/history.html"},
        name="payments_history"
    ),
)
