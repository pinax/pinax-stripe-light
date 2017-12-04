![](http://pinaxproject.com/pinax-design/patches/pinax-stripe.svg)

# Pinax Stripe

[![](https://img.shields.io/pypi/v/pinax-stripe.svg)](https://pypi.python.org/pypi/pinax-stripe/)
[![](https://img.shields.io/badge/license-MIT-blue.svg)](https://pypi.python.org/pypi/pinax-stripe/)

[![Codecov](https://img.shields.io/codecov/c/github/pinax/pinax-stripe.svg)](https://codecov.io/gh/pinax/pinax-stripe)
[![CircleCI](https://circleci.com/gh/pinax/pinax-stripe.svg?style=svg)](https://circleci.com/gh/pinax/pinax-stripe)
![](https://img.shields.io/github/contributors/pinax/pinax-stripe.svg)
![](https://img.shields.io/github/issues-pr/pinax/pinax-stripe.svg)
![](https://img.shields.io/github/issues-pr-closed/pinax/pinax-stripe.svg)

[![](http://slack.pinaxproject.com/badge.svg)](http://slack.pinaxproject.com/)

This app was formerly called `django-stripe-payments` and has been renamed to
avoid namespace collisions and to have more consistency with Pinax.

## Pinax

Pinax is an open-source platform built on the Django Web Framework. It is an ecosystem of reusable Django apps and starter project templates.
This collection can be found at http://pinaxproject.com.

This app was developed as part of the Pinax ecosystem but is just a Django app and can be used independently of other Pinax apps.


## pinax-stripe

`pinax-stripe` is a payments Django app for Stripe.

This app allows you to process one off charges as well as signup users for
recurring subscriptions managed by Stripe.

To bootstrap your project, we recommend you start with:
https://pinax-stripe.readthedocs.org/en/latest/user-guide/getting-started/

## Development

`pinax-stripe` supports a variety of Python and Django versions. It's best if you test each one of these before committing. Our [Travis CI Integration](https://travis-ci.org/pinax/pinax-stripe) will test these when you push but knowing before you commit prevents from having to do a lot of extra commits to get the build to pass.

### Environment Setup

In order to easily test on all these Pythons and run the exact same thing that Travis CI will execute you'll want to setup [pyenv](https://github.com/yyuu/pyenv) and install the Python versions outlined in [tox.ini](tox.ini).

If you are on the Mac, it's recommended you use [brew](http://brew.sh/). After installing `brew` run:

```
$ brew install pyenv pyenv-virtualenv pyenv-virtualenvwrapper
```

Then:

```
$ CFLAGS="-I$(xcrun --show-sdk-path)/usr/include -I$(brew --prefix openssl)/include" \
LDFLAGS="-L$(brew --prefix openssl)/lib" \
pyenv install 2.7.14 3.4.7 3.5.4 3.6.3

$ pyenv virtualenv 2.7.14
$ pyenv virtualenv 3.4.7
$ pyenv virtualenv 3.5.4
$ pyenv virtualenv 3.6.3
$ pyenv global 2.7.14 3.4.7 3.5.4 3.6.3

$ pip install detox
```

To run test suite:

Make sure you are NOT inside a `virtualenv` and then:

```
$ detox
```

This will execute the testing matrix in parallel as defined in the `tox.ini`.


## Documentation

The `pinax-stripe` documentation is available at http://pinax-stripe.readthedocs.org/en/latest/.
The Pinax documentation is available at http://pinaxproject.com/pinax/.
We recently did a Pinax Hangout on pinax-stripe, you can read the recap blog post and find the video [here](http://blog.pinaxproject.com/2016/01/27/recap-january-pinax-hangout/).


## Contribute

See [this blog post](http://blog.pinaxproject.com/2016/02/26/recap-february-pinax-hangout/) including a video, or our [How to Contribute](http://pinaxproject.com/pinax/how_to_contribute/) section for an overview on how contributing to Pinax works. For concrete contribution ideas, please see our [Ways to Contribute/What We Need Help With](http://pinaxproject.com/pinax/ways_to_contribute/) section.

In case of any questions we recommend you [join our Pinax Slack team](http://slack.pinaxproject.com) and ping us there instead of creating an issue on GitHub. Creating issues on GitHub is of course also valid but we are usually able to help you faster if you ping us in Slack.

We also highly recommend reading our [Open Source and Self-Care blog post](http://blog.pinaxproject.com/2016/01/19/open-source-and-self-care/).


## Code of Conduct

In order to foster a kind, inclusive, and harassment-free community, the Pinax Project has a code of conduct, which can be found [here](http://pinaxproject.com/pinax/code_of_conduct/). We ask you to treat everyone as a smart human programmer that shares an interest in Python, Django, and Pinax with you.


## Pinax Project Blog and Twitter

For updates and news regarding the Pinax Project, please follow us on Twitter at @pinaxproject and check out our [blog]( http://blog.pinaxproject.com).
