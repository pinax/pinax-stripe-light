.. _templatetags:


Template Tags
=============

There are two inclusion tags to make it easy to put various forms
within your templates.

change_plan_form
----------------

:template: payments/_change_plan_form.html
:context: `form`, which is an instance of the `payments.forms.ChangePlanForm`


subscribe_form
--------------

:template: payments/_subscribe_form.html
:context: `form`, which is an instance of the `payments.forms.SubscribeForm`; `plans`, which is the `settings.PAYMENTS_PLANS` dictionary

