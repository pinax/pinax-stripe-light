# Templates

Default templates are provided by the `pinax-templates` app in the
[stripe](https://github.com/pinax/pinax-templates/tree/master/pinax/templates/templates/pinax/stripe)
section of that project.

Reference pinax-templates
[installation instructions](https://github.com/pinax/pinax-templates/blob/master/README.md#installation)
to include these templates in your project.

## Customizing Templates

Override the default `pinax-templates` templates by copying them into your project
subdirectory `pinax/stripe/` on the template path and modifying as needed.

For example if your project doesn't use Bootstrap, copy the desired templates
then remove Bootstrap and Font Awesome class names from your copies.
Remove class references like `class="btn btn-success"` and `class="icon icon-pencil"` as well as
`bootstrap` from the `{% load i18n bootstrap %}` statement.
Since `bootstrap` template tags and filters are no longer loaded, you'll also need to update
`{{ form|bootstrap }}` to `{{ form }}` since the "bootstrap" filter is no longer available.

### `base.html`

### `invoice_list.html`

### `paymentmethod_create.html`

### `paymentmethod_delete.html`

### `paymentmethod_list.html`

### `paymentmethod_update.html`

### `subscription_create.html`

### `subscription_delete.html`

### `subscription_form.html`

### `subscription_list.html`

### `subscription_update.html`

### `_invoice_table.html`

### `_stripe_js.html`
