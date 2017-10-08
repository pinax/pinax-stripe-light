# Using Stripe Connect

[Stripe Connect](https://stripe.com/connect) allows you to perform charges on behalf of your
users and then payout to thier bank accounts.

There are several ways to integrate Connect and these result in the creation of different
[account types](https://stripe.com/connect/account-types). Before you begin your Connect
integration, it is crucial you identify which strategy makes sense for your project as which
you choose has great implications in terms of development effort and how much of your users'
experience you can customize.

This project allows use of any account type.

!!! tip "Using Connect requires you to receive webhooks"

    Regardless of which integration you use you will need to enable webhooks. Stripe will
    need to be able to send you account creation and update events which will let you know
    when an account exists and what its verification status is.


## Standard

Users go through an OAuth-like flow hosted by Stripe and set up their own Stripe account.
Stripe will send an event via webhook that will create the account instance in your database.

You can then create a credit card charge on behalf of a standard account by specifying
the `destination_account` parameter:

```python
from pinax.stripe.models import Account
from pinax.stripe.actions.charges import create

account = Account.objects.get(pk=123)
charge = create(5.00, customer, destination_account=account.stripe_id)
```

As a result doing this, the charge will be deposited into the specified Account and
paid out to the user via their configured payout settings.


## Express

Express is meant to be a middle-ground between Standard and Custom, getting you going
quickly but still allowing for a fair bit of UX customization. There are no notable
differences to using Express accounts in comparison to Standard accounts - it's really
just the setup flow that differs.


## Custom

Custom accounts are created, updated and transacted with fully via Stripe's APIs. This
gives you full control over the user experience but places a high developmental burden
on your project.

You must collect information from your users to setup their Accounts. To this end, this
library includes forms that will help you create accounts and keep them verified.

### Verification of Custom accounts

When you create a custom Connect account, you can initially supply the minimum details
and immediately be able to transfer funds to the account. After a certain amount has
been transferred, Stripe will request further verification for an account and at this
point you need to ask your user to supply that information. One of the main advantages
of going the Standard or Express routes is that this verification dialogue happens
between your customer and Stripe.

### Forms

Give an example of the initial account details capturing.

Give an example of `needed_fields` being set to not null and using the extra
details form to capture them.

