# Upgrading from Django Stripe Payments

There has been a tremendous amount of change since this package was called
`django-stripe-payments`. A lot of work and thought has been done to consider
the upgrade path and make it as easy as possible. In terms of the data
migration it should be mostly automatic.

The only data that needs to migrate is the user to customer linkage and that is
done in the [0002_auto_20151205_1451.py](https://github.com/pinax/pinax-stripe/blob/master/pinax/stripe/migrations/0002_auto_20151205_1451.py)
data migration.

This only copies over the customer links. To pull in all the other data you
should run `manage.py sync_plans` and then `manage.py sync_customers`.

That should be it. If you run into any issues upgrading or otherwise, please
[report an issue](https://github.com/pinax/pinax-stripe/issues/new).
