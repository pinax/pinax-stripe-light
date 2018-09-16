# Using Stripe Connect

[Stripe Connect](https://stripe.com/connect) allows you to perform charges on behalf of your
users and then payout to their bank accounts.

There are several ways to integrate Connect and these result in the creation of different
[account types](https://stripe.com/connect/account-types). Before you begin your Connect
integration, it is crucial you identify which strategy makes sense for your project as which
you choose has great implications in terms of development effort and how much of your users'
experience you can customize.

This project allows use of any account type.

!!! tip "Using Connect requires you to receive webhooks"

    Regardless of which integration you use you will need to enable webhooks so that you can
    immediately know when an Account has changed. It may also be necessary for Standard and
    Express integrations in order to detect when an Account has been created.

The minimum required Stripe API version for using the Connect integration with
this project is [version 2017-05-26](https://stripe.com/docs/upgrades#2017-05-25).

## Standard and Express Accounts

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


## Custom Accounts

Custom accounts are created, updated and transacted with fully via Stripe's APIs. This
gives you full control over the user experience but places a high developmental burden
on your project.

You must collect information from your users to setup their Accounts. To this end, this
library includes forms that will help you create accounts and keep them verified.

### Verification

When you create a custom Connect account, you can initially supply the minimum details
and immediately be able to transfer funds to the account. After a certain amount has
been transferred, Stripe will request further verification for an account and at this
point you need to ask your user to supply that information. One of the main advantages
of going the Standard or Express routes is that this verification dialogue happens
between your customer and Stripe.

### Forms

To create a Custom account, you must capture your users' banking information and supply it
to Stripe. The information you must capture varies by country. Be sure to read Stripe's
[documentation on required info](https://stripe.com/docs/connect/required-verification-information)
before proceeding.

This library includes two forms intended to ease the process of collecting the right information
from your users when both creating and updating Custom accounts.

#### Creating a Custom Account

To create an Account for the currently logged in user, you can use the `InitialCustomAccountForm`
along with a `FormView`, as below. Assuming the user enters valid data, this form
will create a custom Account that you can immediately begin processing charges for and paying out
to.

```python
from django.views.generic.edit import FormView
from pinax.stripe.forms import InitialCustomAccountForm


class CreateCustomAccountView(FormView):
    """Prompt a user to enter their bank account details."""

    form_class = InitialCustomAccountForm
    template_name = '<path to your template>'

    def get_form_kwargs(self):
        form_kwargs = super(
            CreateCustomAccountView, self
        ).get_form_kwargs()
        initial = form_kwargs.pop('initial', {})
        form_kwargs['request'] = self.request
        form_kwargs['country'] = 'US'
        return form_kwargs

    def form_valid(self, form):
        try:
            form.save()
        except:
             if form.errors:
                 # means we've converted the exception into errors on the
                 # form so we just redisplay the form in this case
                 return self.form_invalid(form)
             else:
                 # some untranslatable error occurred, log it and
                 # inform user you're looking into it
                 pass
        else:
            # success
            pass
        # redirect to success url
        return super(self, CreateCustomAccountView).form_valid(form)

```

#### Updating a Custom Account with Further Verification Information

After a Custom account has had a certain amount of charges created or funds paid out
Stripe will request additional verification info. They will set a due date after which
the ability to create charges for and pay out to this account may be restricted.

You will need to detect the webhook for `account.updated` and based on several fields,
determine whether or not you need to initiate an information collection process for
your user. For example:

```python
from pinax.stripe.models import Account
from pinax.stripe.signals import WEBHOOK_SIGNALS


@receiver(WEBHOOK_SIGNALS["account.updated"])
@receiver_switch
def stripe_account_updated(sender, event, **kwargs):
    account = Account.objects.get(
        stripe_id=event.validated_message['data']['object']['id']
    )
    # if this is not a custom account, it's probably our platform
    # account or an express or standard account, so do nothing
    if not account.type == "custom":
        return
    if account.verification_due_by and account.verification_fields_needed:
        # then Stripe is asking us for some info!
        # notify the user about this, flag their account so when they login
        # they can see they need to enter further info
        pass

```

When the user next accesses your website, you will want to be able to request
them to provide further information if they wish to continue receiving payments
and possibly payouts.

This library includes the `AdditionalCustomAccountForm` in order to make it easy
to dynamically request the right extra information from the user. Using a `FormView`
as with the previous example, you simply need to initialize the form with a keyword
argument `account`, which should be the Account instance you need to collect
further information for. This form will automatically parse `Account.verification_fields_needed`
and build the fields dynamically.


```python
from django.views.generic.edit import FormView
from pinax.stripe.forms import AdditionalCustomAccountForm


class UpdateCustomAccountView(FormView):
    """Prompt a user to enter further info to keep their account verified."""

    form_class = AdditionalCustomAccountForm
    template_name = '<path to your template>'

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super(
            UpdateCustomAccountView, self
        ).get_form_kwargs(
            *args, **kwargs
        )
        initial = form_kwargs.pop('initial', {})
        form_kwargs['account'] = <Account instance>
        return form_kwargs

    def form_valid(self, form):
        try:
            form.save()
        except:
             if form.errors:
                 # means we've converted the exception into errors on the
                 # form so we just redisplay the form in this case
                 return self.form_invalid(form)
             else:
                 # some untranslatable error occurred, log it and
                 # inform user you're looking into it
                 pass
        else:
            # success
            pass
        # redirect to success url
        return super(self, UpdateCustomAccountView).form_valid(form)

```

#### Manually paying out a Custom account

You may decide to keep your users' payout schedules simple and on a rolling basis, but
using Custom accounts frees you up to fully control this aspect of your product.

When you have a user with a Custom account in good standing, you can create a payout for
the user as below. For the sake of this example, we'll assume you're using the `destination_account`
parametre when creating the charges, such that the payment balance is automatically being
deposited into the Custom account's balance.

```python
from pinax.stripe.models import Account

account = Account.objects.get(pk=<target account id>)

# we choose the first external account the user has configured
external_account = stripe_account.external_accounts.data[0]

external_transfer = transfers.create(
    5.00,
    'USD',
    external_account.id,
    "A payout to a bank account!",
    stripe_account=account.stripe_id,  # this tells Stripe to transfer from the balance of the Custom account
)
assert external_transfer.status in ('paid', 'pending')

```

In most cases, the transfer (to an external account, these are commonly referred to as `payouts`) will be
initially in a `pending` state. After several days, this will shift to `paid` and your user should see the
amount on their bank account statement.

#### Create a Connected Customer

The action `actions.customer.create` accepts a stripe\_account parameter that will automatically
populate a `UserAccount` entry to maintain the relationship between your user and the Stripe account.
Note that in the context of stripe Connect a user is allowed to have several customers, one per account.
This is why the M2M through model `UserAccount` is preferred over `Customer.user` to maintain this
relationships.

```python
customer = pinax.stripe.actions.customers.create(user, stripe_account=account)
UserAccount.filter(user=user, account=account, customer=customer).exists()
>>> True
```

### Retrieve a Connected Customer

```python
customer = pinax.stripe.actions.customers.get_customer_for_user(user, stripe_account=account)

# Under the hood, the M2M through model will be used to filter the relevant customer among all candidates

customer = user.customers.get(user_account__account=stripe_account)
```
