# Template tags

## stripe

#### stripe_public_key

Returns the value of the `PINAX_STRIPE_PUBLIC_KEY` setting as a Javascript
single quoted string. This value can be used to initialize the Stripe
Javascript library. For example:

    {% load stripe %}
    ...
    <script>
        Stripe.setPublishableKey({% stripe_public_key %});
    </script>

will generate:

    <script>
        Stripe.setPublishableKey('pk_<your public key here>');
    </script>

If `PINAX_STRIPE_PUBLIC_KEY` has not been defined, the value
`*** PINAX_STRIPE_PUBLIC_KEY NOT SET ***` is returned **unquoted**. This
will force a JavaScript syntax error to be raised wherever it has been used.
