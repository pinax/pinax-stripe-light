from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    "payments.views",
    url(r"^webhook/$", "webhook", name="payments_webhook"),
    
    url(r"^ajax/subscribe/$", "subscribe", name="payments_subscribe"),
    url(r"^ajax/change/card/$", "change_card", name="payments_change_card"),
    url(r"^ajax/change/plan/$", "change_plan", name="payments_change_plan"),
    url(r"^ajax/cancel/$", "cancel_subscription", name="payments_cancel"),
)
