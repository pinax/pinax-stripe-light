# Actions

## Charges

#### pinax.stripe.actions.charges.calculate_refund_amount

Calculates the refund amount given a charge and optional amount.

Args:

- charge: a `pinax.stripe.models.Charge` object.
- amount: optionally, the `decimal.Decimal` amount you wish to refund.

#### pinax.stripe.actions.charges.capture

Capture the payment of an existing, uncaptured, charge.

Args:
    
- charge: a `pinax.stripe.models.Charge` object.
- amount: the `decimal.Decimal` amount of the charge to capture.

#### pinax.stripe.actions.charges.create

Creates a charge for the given customer.

Args:

- amount: should be a `decimal.Decimal` amount.
- customer: the Stripe id of the customer to charge.
- source: the Stripe id of the source belonging to the customer. Defaults to `None`.
- currency: the currency with which to charge the amount in. Defaults to `"usd"`.
- description: a description of the charge. Defaults to `None`.
- send_receipt: send a receipt upon successful charge. Defaults to 
    `PINAX_STRIPE_SEND_EMAIL_RECEIPTS`.
- capture: immediately capture the charge instead of doing a pre-authorization. 
    Defaults to `True`.

Returns: `pinax.stripe.models.Charge` object.

#### pinax.stripe.actions.charges.sync_charges_for_customer

Populate database with all the charges for a customer.

Args:

- customer: a `pinax.stripe.models.Customer` object

#### pinax.stripe.actions.charges.sync_charge_from_stripe_data

Create or update the charge represented by the data from a Stripe API query.

Args:

- data: the data representing a charge object in the Stripe API

Returns: `pinax.stripe.models.Charge` object

## Customers

#### pinax.stripe.actions.customer.can_charge

Can the given customer create a charge

Args:

- customer: a `pinax.stripe.models.Customer` object

#### pinax.stripe.actions.customer.create

Creates a Stripe customer

Args:

- user: a `user` object.
- card: optionally, the `token` for a new card.
- plan: a plan to subscribe the user to. Defaults to 
    `settings.PINAX_STRIPE_DEFAULT_PLAN`.
- charge_immediately: whether or not the user should be immediately
    charged for the subscription. Defaults to `True`.
- quantity: the quantity of the subscription. Defaults to `1`.

Returns: `pinax.stripe.models.Customer` object that was created

#### pinax.stripe.actions.customer.get_customer_for_user

Get a customer object for a given user

Args:

- user: a `user` object

Returns: `pinax.stripe.models.Customer` object

#### pinax.stripe.actions.customer.purge

Deletes the Stripe customer data and purges the linking of the transaction
data to the Django user.

Args:

- customer: the `pinax.stripe.models.Customer` object to purge.

#### pinax.stripe.actions.customer.link_customer

Links a customer referenced in a webhook event message to the event object

Args:

- event: the `pinax.stripe.models.Event` object to link

#### pinax.stripe.actions.customer.set_default_source

Sets the default payment source for a customer

Args:

- customer: a `pinax.stripe.models.Customer` object
- source: the Stripe ID of the payment source

#### pinax.stripe.actions.customer.sync_customer

Syncronizes a local Customer object with details from the Stripe API

Args:

- customer: a `pinax.stripe.models.Customer` object
- cu: optionally, data from the Stripe API representing the customer

## Events

#### pinax.stripe.actions.events.add_event

Adds and processes an event from a received webhook

Args:

- stripe_id: the stripe id of the event.
- kind: the label of the event.
- livemode: `True` or `False` if the webhook was sent from livemode or not.
- message: the data of the webhook.
- api_version: the version of the Stripe API used.
- request_id: the id of the request that initiated the webhook.
- pending_webhooks: the number of pending webhooks. Defaults to `0`.

#### pinax.stripe.actions.events.dupe_event_exists

Checks if a duplicate event exists

Args:

- stripe_id: the Stripe ID of the event to check.

Returns: `True`, if the event already exists, otherwise, `False`.

## Exceptions

#### pinax.stripe.actions.exceptions.log_exception

Log an exception that was captured as a result of processing events

Args:

- data: the data to log about the exception
- exception: the exception object itself
- event: optionally, the event object from which the exception occurred

## Invoices

#### pinax.stripe.actions.invoices.create

Creates a Stripe invoice

Args:

- customer: the `pinax.stripe.models.Customer` to create the invoice for.

Returns: the data from the Stripe API that represents the invoice object that
    was created

#### pinax.stripe.actions.invoices.create_and_pay

Creates and and immediately pays an invoice for a customer

Args:

- customer: the `pinax.stripe.models.Customer` to create the invoice for.

Returns: `True`, if invoice was created, `False` if there was an error.

#### pinax.stripe.actions.invoices.pay

Triggers an invoice to be paid

Args:

- invoice: the `pinax.stripe.models.Invoice` object to have paid
- send_receipt: if `True`, send the receipt as a result of paying. Defaults to `True`.

Returns: `True` if the invoice was paid, `False` if it was unable to be paid.

#### pinax.stripe.actions.invoices.sync_invoice_from_stripe_data

Syncronizes a local invoice with data from the Stripe API

Args:
    
- stripe_invoice: data that represents the invoice from the Stripe API
- send_receipt: if `True`, send the receipt as a result of paying. Defaults
    to `settings.PINAX_STRIPE_SEND_EMAIL_RECEIPTS`.

Returns: the `pinax.stripe.models.Invoice` that was created or updated

#### pinax.stripe.actions.invoices.sync_invoices_for_customer

Syncronizes all invoices for a customer

Args:

- customer: the `pinax.stripe.models.Customer` for whom to syncronize all invoices

#### pinax.stripe.actions.invoices.sync_invoice_items

Syncronizes all invoice line items for a particular invoice

This assumes line items from a Stripe invoice.lines property and not through
the invoicesitems resource calls. At least according to the documentation
the data for an invoice item is slightly different between the two calls.

For example, going through the invoiceitems resource you don't get a "type"
field on the object.

Args:

- invoice: the `pinax.stripe.models.Invoice` object to syncronize
- items: the data from the Stripe API representing the line items

## Plans

#### pinax.stripe.actions.plans.sync_plans

Syncronizes all plans from the Stripe API

## Refunds

#### pinax.stripe.actions.refunds.create

Creates a refund for a particular charge

Args:

- charge: the `pinax.stripe.models.Charge` against which to create the refund
- amount: how much should the refund be, defaults to `None`, in which case
    the full amount of the charge will be refunded

## Sources

#### pinax.stripe.actions.sources.create_card

Creates a new card for a customer

Args:

- customer: the `pinax.stripe.models.Customer` to create the card for
- token: the token created from Stripe.js

#### pinax.stripe.actions.sources.delete_card

Deletes a card from a customer

Args:

- customer: the `pinax.stripe.models.Customer` to delete the card from
- source: the Stripe ID of the payment source to delete

#### pinax.stripe.actions.sources.delete_card_object

Deletes the local `pinax.stripe.models.Customer` object.

Args:

- source: the Stripe ID of the card

#### pinax.stripe.actions.sources.sync_card

Syncronizes the data for a card locally for a given customer

Args:

- customer: the `pinax.stripe.models.Customer` to create or update a card for
- source: data reprenting the card from the Stripe API

#### pinax.stripe.actions.sources.sync_bitcoin

Syncronizes the data for a Bitcoin receiver locally for a given customer

Args:

- customer: the `pinax.stripe.models.Customer` to create or update a Bitcoin 
    receiver for
- source: data reprenting the Bitcoin receiver from the Stripe API

#### pinax.stripe.actions.sources.sync_payment_source_from_stripe_data

Syncronizes the data for a payment source locally for a given customer

Args:

- customer: the `pinax.stripe.models.Customer` to create or update a Bitcoin 
    receiver for
- source: data reprenting the payment source from the Stripe API

#### pinax.stripe.actions.sources.update_card

Updates a card for a given customer

Args:

- customer: the `pinax.stripe.models.Customer` for whom to update the card
- source: the Stripe ID of the card to update
- name: optionally, a name to give the card
- exp_month: optionally, the expiration month for the card
- exp_year: optionally, the expiration year for the card

## Subscriptions

#### pinax.stripe.actions.subscriptions.cancel

Cancels a subscription

Args:

- subscription: the `pinax.stripe.models.Subscription` to cancel
- at_period_end: True, to cancel at the end, otherwise immediately cancel. 
    Defaults to `True`

#### pinax.stripe.actions.subscriptions.create

Creates a subscription for the given customer

Args:

- customer: the `pinax.stripe.models.Customer` to create the subscription for
- plan: the plan to subscribe to
- quantity: if provided, the number to subscribe to
- trial_days: if provided, the number of days to trial before starting
- token: if provided, a token from Stripe.js that will be used as the
    payment source for the subscription and set as the default
    source for the customer, otherwise the current default source
    will be used
- coupon: if provided, a coupon to apply towards the subscription
- tax_percent: if provided, add percentage as tax 

Returns: the `pinax.stripe.models.Subscription` object that was created

#### pinax.stripe.actions.subscriptions.has_active_subscription

Checks if the given customer has an active subscription

Args:

- customer: the `pinax.stripe.models.Subscription` to check

Returns: `True`, if there is an active subscription, otherwise `False`

#### pinax.stripe.actions.subscriptions.is_period_current

Tests if the provided `pinax.stripe.models.Subscription` object for the current period

Args:

- subscription: a `pinax.stripe.models.Subscription` object to test

Returns: `True`, if provided subscription periods end is beyond `timezone.now`,
    otherwise `False`.

#### pinax.stripe.actions.subscriptions.is_status_current

Tests if the provided subscription object has a status that means current

Args:

- subscription: a `pinax.stripe.models.Subscription` object to test

Returns: `bool`

#### pinax.stripe.actions.subscriptions.is_valid

Tests if the provided subscription object is valid

Args:

- subscription: a `pinax.stripe.models.Subscription` object to test

Returns: `bool`

#### pinax.stripe.actions.subscriptions.retrieve

Retrieve a subscription object from Stripe's API

Stripe throws an exception if a subscription has been deleted that we are
attempting to sync. In this case we want to just silently ignore that
exception but pass on any other.

Args:

- customer: the `pinax.stripe.models.Customer` who's subscription you are 
    trying to retrieve
- sub_id: the Stripe ID of the subscription you are fetching

Returns: the data for a subscription object from the Stripe API

#### pinax.stripe.actions.subscriptions.sync_subscription_from_stripe_data

Syncronizes data from the Stripe API for a subscription

Args:

- customer: the `pinax.stripe.models.Customer` who's subscription you are 
    syncronizing
- subscription: data from the Stripe API representing a subscription

Returns: the `pinax.stripe.models.Subscription` object created or updated

#### pinax.stripe.actions.subscriptions.update

Updates a subscription

Args:

- subscription: the `pinax.stripe.models.Subscription` to update
- plan: optionally, the plan to change the subscription to
- quantity: optionally, the quantiy of the subscription to change
- prorate: optionally, if the subscription should be prorated or not. Defaults
    to `True`
- coupon: optionally, a coupon to apply to the subscription
- charge_immediately: optionally, whether or not to charge immediately. 
    Defaults to `False`

## Transfers

#### pinax.stripe.actions.transfers.during

Return a queryset of `pinax.stripe.models.Transfer` objects for the provided
year and month.

Args:

- year: 4-digit year
- month: month as a integer, 1=January through 12=December

#### pinax.stripe.actions.transfers.sync_transfer

Syncronizes a transfer from the Stripe API

Args:

- transfer: data from Stripe API representing transfer
- event: the `pinax.stripe.models.Event` associated with the transfer

#### pinax.stripe.actions.transfers.update_status

Updates the status of a `pinax.stripe.models.Transfer` object from Stripe API

Args:

- transfer: a `pinax.stripe.models.Transfer` object to update
