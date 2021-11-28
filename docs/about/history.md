# History

This app started as `django-stripe-payments` on **August 18, 2012** and was
written by Eldarion from their direct experience at building SaaS and eCommerce
applications. It was [announced](http://eldarion.com/blog/2012/10/23/easily-add-stripe-payments-your-django-site/)
as a reusable app on **October 23, 2012**.

Exactly 2 years and one day later, on **October 24, 2014**, Eldarion [donated django-stripe-payments](http://eldarion.com/blog/2014/10/28/eldarion-donates-django-stripe-payments-pinax/)
to [Pinax](http://pinaxproject.com).

On **November 12, 2015** after many months of design considerations and procrastinating,
the Pinax team did a major refactor bring test coverage up to 100%, adding lots
of docs, and re-architecting into a service layer for a better API and easier
maintenance and testability.

After nearly 200 commits, 13 merged pull requests, and 45 closed issues,
`pinax-stripe` was to publish on **December 5, 2015**. Though it's a rename,
we are kept the same semantic versioning from `django-stripe-payments` making
this release the `3.0.0` release.

On **November 27, 2021**, after years of use in many different sites, it was decided
to narrow the scope of the package to the parts that actually were getting used.
The package adopted a new name, `pinax-stripe-light` in case someone wants to pick
up the maintainence on the original larger vision for the project.

Years ago, it was [hard forked](https://github.com/dj-stripe/dj-stripe/commit/6fe7b7970f8282e2f5606468f5ac5bc5e226458f), violating terms of our license [due to leaving out the attribution](https://github.com/dj-stripe/dj-stripe/commit/6fe7b7970f8282e2f5606468f5ac5bc5e226458f#diff-c693279643b8cd5d248172d9c22cb7cf4ed163a3c98c8a3f69c2717edd3eacb7) producing [dj-stripe](https://github.com/dj-stripe/dj-stripe/).

Despite this violation, we recommend considering this
package if you need a fuller package to integrate with Stripe.  It has commercial
support and is well-maintained at the time of writing this.
