import datetime
import decimal

from django.conf import settings
from django.utils import timezone


def convert_tstamp(response, field_name=None):
    tz = timezone.utc if settings.USE_TZ else None

    if field_name and response.get(field_name):
        return datetime.datetime.fromtimestamp(
            response[field_name],
            tz
        )
    if response is not None and not field_name:
        return datetime.datetime.fromtimestamp(
            response,
            tz
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


CURRENCY_SYMBOLS = {
    "aud": "\u0024",
    "cad": "\u0024",
    "chf": "\u0043\u0048\u0046",
    "cny": "\u00a5",
    "eur": "\u20ac",
    "gbp": "\u00a3",
    "jpy": "\u00a5",
    "myr": "\u0052\u004d",
    "sgd": "\u0024",
    "usd": "\u0024",
}


def obfuscate_secret_key(secret_key):
    return "*" * 20 + secret_key[-4:]
