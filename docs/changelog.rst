.. _changelog:

ChangeLog
=========

2.0
---

* refactored models to be in line with api changes
* added a new setting to enable setting the API version
* added new event types to webhook signals
* handle the transfer.update webhook
* added ability to sync customer data


1.3
---

* removed tag.js
* fixed bugs in template tags due to missing forms
* updated included templates to be ready for checkout.js integration

1.2.2
-----

* handle deprected 'diputed' property on charges

1.2.1
-----

* upgraded stripe library requirement to 1.7.9

1.2
---

* added better admin for Charge
* do not raise exception if customer is deleted first in Stripe
* updated install notes

1.1.1
-----

* Update to stripe 1.7.7
* Handle case of some charge messages not getting attached to their invoice

1.1
---

1.0
---

* initial release
