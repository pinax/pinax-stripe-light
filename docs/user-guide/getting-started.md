# Getting Started

## Installation

To install simply run:

    pip install pinax-stripe

## Configuration

In your `settings.py` add `pinax.stripe` to your `INSTALLED_APPS` setting:

    # settings.py
    INSTALLED_APPS += ["pinax.stripe"]


Then setup your Stripe keys. It's a good idea not to commit your production
keys to your source repository as a way of limiting access to who can access
your Stripe account.  One of doing this is just setting environment variables
where you deploy your code:

    # settings.py
    PINAX_STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "your test public key")
    PINAX_STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "your test secret key")


This will use the environment variables `STRIPE_PUBLIC_KEY` and
`STRIPE_SECRET_KEY` if they have been set otherwise what you set in the second
parameter will be used as default.

If you are using `pinax-stripe` in drive something like a Software-as-a-Service
site with subscriptions, then you will want to also set the Stripe ID for on a
`PINAX_STRIPE_DEFAULT_PLAN` setting and install middleware. We will cover this
in more detail in the [SaaS Guide](../user-guide/saas.md).

If you want to use the [default views](../reference/views.md) that ship with
`pinax-stripe` you will need to hook up the urls:

    # urls.py
    url(r"^payments/", include("pinax.stripe.urls"),


However you may only want to hook up some of them or customize some and hook up
each url individually. Please see the [urls](../reference/urls.md) docs for more
details.


## Syncing Data

The data in `pinax-stripe` is largely a form of a cache of the data you have
in your Stripe account.  The one exception to this is the `pinax.stripe.models.Customer` model that links a Stripe Customer to a user in
your site.

### Syncing Plans

If you are using subscriptions you'll want to setup your plans in your Stripe
account and then run:

    ./manage.py sync_plans


### Initializing Customers

If you already have users in your site and are adding payments and/or
subscription capabilities and want to create a customer for every user in your
site, you'll want to do two things:

First setup, handle new users being created in your site either in a sign up
view, a signal receiver, etc., to run:

    from pinax.stripe.actions import customers
    customers.create(user=new_user)

Then, to update your Stripe account after your initial deploy of a site with
existing users:

    ./manage.py init_customers


### Syncing Customer Data

Note, however, this is not required and you may choose to only create customers
for users that actually become customers in the event you have a mix of users
and customers on your site.

In the event, you need to update the local cache of data for your customers,
you can run:

    ./manage.py sync_customers
