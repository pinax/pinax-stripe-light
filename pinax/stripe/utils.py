import datetime
import decimal

from django.utils import timezone


def convert_tstamp(response, field_name=None):
    if field_name and response.get(field_name):
        return datetime.datetime.fromtimestamp(
            response[field_name],
            timezone.utc
        )
    if response is not None and not field_name:
        return datetime.datetime.fromtimestamp(
            response,
            timezone.utc
        )


# currencies those amount=1 means 100 cents
# https://support.stripe.com/questions/which-zero-decimal-currencies-does-stripe-support
ZERO_DECIMAL_CURRENCIES = [
    "bif", "clp", "djf", "gnf", "jpy", "kmf", "krw",
    "mga", "pyg", "rwf", "vuv", "xaf", "xof", "xpf",
]


def convert_amount_for_db(amount, currency="usd"):
    if currency is None:  # @@@ not sure if this is right; find out what we should do when API returns null for currency
        currency = "usd"
    return (amount / decimal.Decimal("100")) if currency.lower() not in ZERO_DECIMAL_CURRENCIES else decimal.Decimal(amount)


def convert_amount_for_api(amount, currency="usd"):
    if currency is None:
        currency = "usd"
    return int(amount * 100) if currency.lower() not in ZERO_DECIMAL_CURRENCIES else int(amount)


def update_with_defaults(obj, defaults, created):
    if not created:
        for key in defaults:
            setattr(obj, key, defaults[key])
        obj.save()
    return obj
