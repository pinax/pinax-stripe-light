# Release Notes

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
