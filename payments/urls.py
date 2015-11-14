from django.conf.urls import url

try:
    from account.decorators import login_required
except ImportError:
    from django.contrib.auth.decorators import login_required

from .views import (
    CancelView,
    ChangeCardView,
    ChangePlanView,
    HistoryView,
    SubscribeView,
    Webhook,
    AjaxSubscribe,
    AjaxChangeCard,
    AjaxChangePlan,
    AjaxCancelSubscription
)


urlpatterns = [
    url(r"^webhook/$", Webhook.as_view(), name="payments_webhook"),
    url(r"^a/subscribe/$", login_required(AjaxSubscribe.as_view()), name="payments_ajax_subscribe"),
    url(r"^a/change/card/$", login_required(AjaxChangeCard.as_view()), name="payments_ajax_change_card"),
    url(r"^a/change/plan/$", login_required(AjaxChangePlan.as_view()), name="payments_ajax_change_plan"),
    url(r"^a/cancel/$", login_required(AjaxCancelSubscription.as_view()), name="payments_ajax_cancel"),
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
]
