# URLs

Default URLs are provided for basic management of subscriptions, payment methods and payment history.

```
# urls.py
url(r"^payments/", include("payments.urls")),
```

You many want to customize urls or override them according to the needs of your application.
The Webhook url, `url(r"^webhook/$", Webhook.as_view(), name="pinax_stripe_webhook"),` is the url
that Stripe will be sending requests to for updating Stripe data.  The remainder of the urls
are provided for interacting with subscriptions, payment methods and payment history.

