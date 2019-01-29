# eCommerce

One very rudimentary and small aspect of eCommerce is making one off charges.
There is a lot to write about in using `pinax-stripe` for eCommerce, but at
the most basic level making a one off charge can be done with the following
bit of Python code in your site:

```python
import decimal

from pinax.stripe.actions import charges


charges.create(
    amount=decimal.Decimal("5.66"),
    customer=request.user.customer.stripe_id
)
```

This will create a charge on the customer's default payment source for $5.66.
