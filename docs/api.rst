.. _api:

API
===

The views in django-stripe-payments are intentionally very thin. In fact, quite
often you might want to implement your own views for some or all of this in your
own site to fit your own integration needs.

The majority of the functionality exists in model methods and is designed to be
consumed throughout your site, in whatever way integration makes sense for you.

Furthermore, all data stored in django-stripe-payments is a local cache of what
exists in Stripe and is fetchable via the Stripe API. Even if you were to
truncate all data in django-stripe-payments, there is no real data loss as you
can pull it all again and load up your models. The important ones have sync
methods to do this for you. Sync methods haven't been written for all models
(yet).


Models
------

`EventProcessingException`
^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a simple model that is just a log of any exceptions encountered while
processing events. It's really not designed to be consumed directly other than
being able to view exceptions in the admin or querying the database.

The `Event` model is the only object that uses this model.


`Event`
^^^^^^^

An event is a webhook message sent from Stripe to the webhook url you set up.

The message is captured in a view, saved to the model. It is then validated and
processed. Processing only occurs if the messages is indeed validated. It's only
valid if the event content pulled by id from Stripe matches what was received
at the webhook endpoint. This is designed to prevent people from discovering
your endpoint url and posting fake data to it.

Processing the event is where all the other models get populated in
django-stripe-payments. Not all message types are processed, but all messages
do send a signal so that you can handle specific messages in your site if you
care about something that django-stripe-payments isn't capturing.

The `Event` model is the work horse of django-stripe-payments, however, it is
not intended to be used directly either.


`Transfer`
^^^^^^^^^^

The `Transfer` model stores records of Stripe transfers into your bank account.

It's a read only object but does have a special manager that provides some
aggregates:

    Transfer.objects.during(year, month)
    Transfer.objects.paid_totals_for(year, month)

The first, `during`, will return a list of transfers for a given year and month,
while the second, `paid_totals_for`, will return a list of aggregates:

* Total Gross
* Total Net
* Total Charge Fees
* Total Adjustment Fees
* Total Refunds
* Total Refund Fees
* Total Validation Fees
* Total Amount


`TransferChargeFee`
^^^^^^^^^^^^^^^^^^^

Stores details about each fee associated with a particular `Transfer`.


`Customer`
^^^^^^^^^^

The `Customer` object maps to a customer record in Stripe and has a nullable
foreign key to a `User` object. It's nullable because you maybe delete a user
from your site but would likely want/need to keep financial record history.

There are lots of public API methods on `Customer` intances that are likely of
some interest.

`purge()`
~~~~~~~~~

This method will set the user foreign key to `None` and set the card details to
blank. The model's `delete()` method is overridden so that it calls `purge()`
instead of destorying the instance in the database as the rest of the models in
django-stripe-payments that have financial details are tied to the `Customer`.

Even if the customer object at this point is anonymous, it is important to not
break the chain of financial details that might be important to you for various
aggregates and other reporting needs.


`CurrentSubscription`
^^^^^^^^^^^^^^^^^^^^^



`Invoice`
^^^^^^^^^



`InvoiceItem`
^^^^^^^^^^^^^



`Charge`
^^^^^^^^
