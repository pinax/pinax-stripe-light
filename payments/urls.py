from django.conf.urls import patterns, url

from django.views.generic import TemplateView

from django.contrib.auth.decorators import login_required

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
        login_required(TemplateView.as_view(template_name="payments/subscribe.html")),
        {
            "extra_context": {"form": PlanForm}
        },
        name="payments_subscribe"
    ),
    url(
        r"^change/card/$",
        login_required(TemplateView.as_view(template_name="payments/change_card.html")),
        name="payments_change_card"
    ),
    url(
        r"^change/plan/$",
        login_required(TemplateView.as_view(template_name="payments/change_plan.html")),
        {
            "extra_context": {"form": PlanForm}
        },
        name="payments_change_plan"
    ),
    url(
        r"^cancel/$",
        login_required(TemplateView.as_view(template_name="payments/cancel.html")),
        name="payments_cancel"
    ),
    url(
        r"^history/$",
        login_required(TemplateView.as_view(template_name="payments/history.html")),
        name="payments_history"
    ),
)
