# Commands

#### pinax.stripe.management.commands.init_customers

Create `pinax.stripe.models.Customer` objects for existing users that do not
have one.

#### pinax.stripe.management.commands.sync_customers

Synchronizes customer data from the Stripe API.

Utilizes the following actions:

- `pinax.stripe.actions.customers.sync_customer`
- `pinax.stripe.actions.invoices.sync_invoices_for_customer`
- `pinax.stripe.actions.charges.sync_charges_for_customer`

#### pinax.stripe.management.commands.sync_plans

Make sure your Stripe account has the plans.

Utilizes `pinax.stripe.actions.plans.sync_plans`.
