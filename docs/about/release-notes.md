# Release Notes

## 4.4.0 - 2018-08-04

* Pin `python-stripe` to `>2.0` after the merge of [PR 574](https://github.com/pinax/pinax-stripe/pull/574) which fixed compatibility. [PR 581](https://github.com/pinax/pinax-stripe/pull/581)


## 4.3.1 - 2018-08-04

* Pin `python-stripe` to `<2.0` as that major release broke things in `pinax-stripe` [PR 580](https://github.com/pinax/pinax-stripe/pull/580)


## 3.4.1 - 2017-04-21

This fixes a bug that was introduced in `3.4.0` with customer creation taking a `quantity` parameter.

* [PR 332](https://github.com/pinax/pinax-stripe/pull/332) ([Ryan Verner](https://github.com/xfxf))


## 3.4.0 - 2017-04-14

This release is long overdue.  It includes coupon support, improved admin,
fixing some bugs and deprecation warnings, support for taxes on subscriptions
and handling unicode in customers names.

* [PR 259](https://github.com/pinax/pinax-stripe/pull/259) ([Vadim](https://github.com/bessiash)) - country is blankable now for `Card` objects
* [PR 292](https://github.com/pinax/pinax-stripe/pull/292) ([Russell Keith-Magee](https://github.com/freakboy3742)) - handle unicode characters in customer names
* [PR 299](https://github.com/pinax/pinax-stripe/pull/299) ([Russell Keith-Magee](https://github.com/freakboy3742)) - add template tag for stripe public key
* [PR 302](https://github.com/pinax/pinax-stripe/pull/302) ([Ryan Verner](https://github.com/xfxf)) - tax support to subscriptions
* [PR 304](https://github.com/pinax/pinax-stripe/pull/304) ([Russell Keith-Magee](https://github.com/freakboy3742)) - enable charge immediately option on subscription update
* [PR 303](https://github.com/pinax/pinax-stripe/pull/303) ([Russell Keith-Magee](https://github.com/freakboy3742)) - coupon support
* [PR 305](https://github.com/pinax/pinax-stripe/pull/305) ([Russell Keith-Magee](https://github.com/freakboy3742)) - protect against duplicate customer creation
* [PR 307](https://github.com/pinax/pinax-stripe/pull/307) ([Adam Duren](https://github.com/adamduren)) - do not require customer to create a charge
* [PR 313](https://github.com/pinax/pinax-stripe/pull/313) ([Ian R-P](https://github.com/iarp)) - update to handle change in exception message from stripe for customer not found
* [PR 316](https://github.com/pinax/pinax-stripe/pull/316) ([Charlie Denton](https://github.com/meshy)) - doc updates
* [PR 317](https://github.com/pinax/pinax-stripe/pull/317) ([Charlie Denton](https://github.com/meshy)) - fixes failed charge webhook processing
* [PR 319](https://github.com/pinax/pinax-stripe/pull/319) ([Charlie Denton](https://github.com/meshy)) - allow customers to be created with qty > 1 of a subscription plan
* [PR 323](https://github.com/pinax/pinax-stripe/pull/323) ([Charlie Denton](https://github.com/meshy)) - fix packaging to prevent jsonfield 2+ from installing
* [PR 324](https://github.com/pinax/pinax-stripe/pull/324) ([Charlie Denton](https://github.com/meshy)) - gracefully handle invoice creation failure
* [PR 295](https://github.com/pinax/pinax-stripe/pull/295), [PR 291](https://github.com/pinax/pinax-stripe/pull/291), [PR 288](https://github.com/pinax/pinax-stripe/pull/288), [PR 286](https://github.com/pinax/pinax-stripe/pull/286) ([Mariusz Felisiak](https://github.com/felixxm)) - fixed deprecation warnings


## 3.3.0 - 2016-10-03

This release saw contributions from 6 people!

* [PR 280](https://github.com/pinax/pinax-stripe/pull/280) ([Dan Olsen](https://github.com/danolsen)) - sync subscription on cancel
* [PR 272](https://github.com/pinax/pinax-stripe/pull/272) ([Tobin Brown](https://github.com/Brobin)) - fix admin filtering for customer admin
* [PR 252](https://github.com/pinax/pinax-stripe/pull/252) ([Chris Streeter](https://github.com/streeter)) - ignore customers who might be test customers
* [PR 283](https://github.com/pinax/pinax-stripe/pull/283) ([Nikolai Konovalov](https://github.com/berdoc)) - fix error raised when `USE_TZ=False`
* [PR 247](https://github.com/pinax/pinax-stripe/pull/247) ([Oli Bates](https://github.com/obates)) - add plan metadata
* [Issue 284](https://github.com/pinax/pinax-stripe/issues/284) ([Patrick Altman](https://github.com/paltman)) - sync subscription data immediately upon subscribe

## 3.2.1 - 2016-07-30

* [PR 266](https://github.com/pinax/pinax-stripe/pull/266) added some docs for webhooks and signals

## 3.2.0 - 2016-07-28

We continue to have a healthy group of contributors helping to maintain and
grow `pinax-stripe`.

* [Graham Ullrich](https://github.com/grahamu)
* [Camden Bickel](https://github.com/camdenb)
* [Patrick Altman](https://github.com/paltman/)
* [Anna Ossowski](https://github.com/ossanna16/)
* [Trevor Watson](https://github.com/cfc603)
* [Chris Streeter](https://github.com/streeter/)

This is mostly fixes and clean up to some bits of documentation but one
enhancement of the removal of Sites framework from being a hard requirement. It
is now optional, though if you are not running Sites framework, you'll want to
override some of the hooks in the `DefaultHookSet` to handle your specific
case.

* added a link to our code of conduct
* added support for wheels in our release packaging
* updated the classifier to Production/Stable (from Alpha!)
* [PR 253](https://github.com/pinax/pinax-stripe/pull/253) - fixed a typo
* [PR 261](https://github.com/pinax/pinax-stripe/pull/261) - fixed a documentation bug
* [PR 263](https://github.com/pinax/pinax-stripe/pull/263) - fixed documentation bug dealing with installation
* [PR 256](https://github.com/pinax/pinax-stripe/pull/256) - conditional sites framework import


## 3.1.0 - 2016-03-25

Thanks to all the contributors that made this release happen, at least 5 of
which were first time contributors to `pinax-stripe`!

* [Patrick Altman](https://github.com/paltman/)
* [Anna Ossowski](https://github.com/ossanna16/)
* [Nicolas Delaby](https://github.com/ticosax/)
* [Chris Streeter](https://github.com/streeter/)
* [Trevor Watson](https://github.com/cfc603/)
* [Michael Warkentin](https://github.com/mwarkentin/)
* [Anirudh S](https://github.com/gingerjoos/)
* [Raphael Deem](https://github.com/r0fls/)
* [Jannis Gebauer](https://github.com/jayfk/)

### Infrastructure

* dropped support for Python 3.2
* [PR 221](https://github.com/pinax/pinax-stripe/pull/221) - modernized tox.ini

### Documentation

* [PR 222](https://github.com/pinax/pinax-stripe/pull/222), [PR 226](https://github.com/pinax/pinax-stripe/pull/226), [PR 232](https://github.com/pinax/pinax-stripe/pull/232), [PR 235](https://github.com/pinax/pinax-stripe/pull/235) - various fixes and minor updates
* [PR 238](https://github.com/pinax/pinax-stripe/pull/238) / [Issue 236](https://github.com/pinax/pinax-stripe/issues/236) - added [migration docs to getting started](../user-guide/getting-started.md)
* [PR 245](https://github.com/pinax/pinax-stripe/pull/245) - added documentation for [actions](../reference/actions.md)
* [PR 246](https://github.com/pinax/pinax-stripe/pull/246) - added documentation for [management commands](../reference/commands.md)

### Enhancements

* [Issue 228](https://github.com/pinax/pinax-stripe/issues/228) - added support for other currency symbols in `Plan` string representation
* [PR 234](https://github.com/pinax/pinax-stripe/pull/234) - added form for validating payment method changes
* [PR 237](https://github.com/pinax/pinax-stripe/pull/237) - added readonly admin for `Plan`
* [PR 239](https://github.com/pinax/pinax-stripe/pull/239) - return objects from sources to enable integration with DRF
* [Issue 240](https://github.com/pinax/pinax-stripe/issues/240) made CVC check value blankable
* [PR 241](https://github.com/pinax/pinax-stripe/pull/241) provided a way to override default behavior of sending a receipt when creating a charge by setting `PINAX_STRIPE_SEND_EMAIL_RECEIPTS`
* [PR 248](https://github.com/pinax/pinax-stripe/pull/248) - support more than default plan page size


## 3.0.0 - 2015-12-05

* renamed to `pinax-stripe`
* service layer for the app API
* 100% test coverage
* supports latest Stripe API
* multiple subscriptions
* multiple payment methods
* documentation improvements
* over 200 commits from 9 contributors
* Python 3 support
* sync plans like rest of Stripe data rather the old `init_plans`
* switch from `django-jsonfield` to `jsonfield`
* dropped support for older versions of Django
* tables namespaced to `pinax_stripe_` prefix and package is now under `pinax.stripe.*` namespace
* handle all current webhooks and completely refactored how webhooks are processed
* removed dependency on using `eldarion-ajax`
* switched to a standard set of class based views instead of opinionated AJAX views
* full set of templates now ship with `pinax-theme-bootstrap`


## 2.0.0 - 2014-09-29



## 2.0b34 - 2013-11-12



## 2.0b33 - 2013-10-24



## 2.0b32 - 2013-09-09



## 2.0b31 - 2013-08-31



## 2.0b30 - 2013-08-31



## 2.0b29 - 2013-08-30



## 2.0b28 - 2013-08-29



## 2.0b27 - 2013-08-20



## 2.0b26 - 2013-08-17



## 2.0b25 - 2013-08-14 *



## 2.0b24 - 2013-08-14



## 2.0b23 - 2013-07-14 *



## 2.0b22 - 2013-06-28



## 2.0b21 - 2013-06-07 *



## 2.0b20 - 2013-05-08



## 2.0b18 - xxx



## 2.0b17 - 2013-05-03 *



## 2.0b16 - 2013-05-03



## 2.0b15 - 2013-05-03



## 2.0b14 - 2013-04-30



## 2.0b13 - 2013-04-23



## 2.0b12 - 2013-04-19



## 1.3 - 2013-02-07 *



## 1.2.2 - 2013-02-07 *



## 1.2.1 - 2013-02-07 *



## 1.2 - 2013-01-20 *



## 1.1.1 - 2012-12-20 *



## 1.1 - 2012-12-17 *



## 1.0 - 2012-10-23 *



## 0.1 - 2012-08-18 *
