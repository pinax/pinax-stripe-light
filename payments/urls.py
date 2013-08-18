from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import (
    CancelView,
    ChangeCardView,
    ChangePlanView,
    HistoryView,
    SubscribeView
)


urlpatterns = patterns(
    "payments.views",
    url(r"^webhook/$", "webhook", name="payments_webhook"),
    url(r"^a/subscribe/$", "subscribe", name="payments_ajax_subscribe"),
    url(r"^a/change/card/$", "change_card", name="payments_ajax_change_card"),
    url(r"^a/change/plan/$", "change_plan", name="payments_ajax_change_plan"),
    url(r"^a/cancel/$", "cancel", name="payments_ajax_cancel"),
    url(
        r"^subscribe/$",
        login_required(SubscribeView.as_view()),
        name="payments_subscribe"
    ),
    url(
        r"^change/card/$",
        login_required(ChangeCardView.as_view()),
        name="payments_change_card"
    ),
    url(
        r"^change/plan/$",
        login_required(ChangePlanView.as_view()),
        name="payments_change_plan"
    ),
    url(
        r"^cancel/$",
        login_required(CancelView.as_view()),
        name="payments_cancel"
    ),
    url(
        r"^history/$",
        login_required(HistoryView.as_view()),
        name="payments_history"
    ),
)
