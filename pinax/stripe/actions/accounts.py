import datetime

import stripe

from .. import models, utils
from .externalaccounts import sync_bank_account_from_stripe_data


def create(user, country, **kwargs):
    """
    Create an Account.

    Args:
        country: two letter country code for where the individual lives

    Returns:
        a pinax.stripe.models.Account object
    """
    kwargs["country"] = country
    stripe_account = stripe.Account.create(**kwargs)
    return sync_account_from_stripe_data(
        stripe_account, user=user
    )


def update(account, data):
    """
    Update the given account with extra data.

    Args:
        account: a pinax.stripe.models.Account object
        data: dict of account fields to update via API:

            first_name         -> legal_entity.first_name
            last_name          -> legal_entity.last_name
            dob                -> legal_entity.dob
            personal_id_number -> legal_entity.personal_id_number
            document           -> legal_entity.verification.document

    Returns:
        a pinax.stripe.models.Account object
    """
    stripe_account = stripe.Account.retrieve(id=account.stripe_id)

    if data.get("dob"):
        stripe_account.legal_entity.dob = data["dob"]

    if data.get("first_name"):
        stripe_account.legal_entity.first_name = data["first_name"]

    if data.get("last_name"):
        stripe_account.legal_entity.last_name = data["last_name"]

    if data.get("personal_id_number"):
        stripe_account.legal_entity.personal_id_number = data["personal_id_number"]

    if data.get("document"):
        response = stripe.FileUpload.create(
            purpose="identity_document",
            file=data["document"],
            stripe_account=stripe_account.id
        )
        stripe_account.legal_entity.verification.document = response["id"]

    stripe_account.save()
    return sync_account_from_stripe_data(stripe_account)


def sync_account(account):
    """
    Update the given local Account instance from remote data.

    Args:
        account: a pinax.stripe.models.Account object

    Returns:
        a pinax.stripe.models.Account object
    """
    stripe_account = stripe.Account.retrieve(id=account.stripe_id)
    return sync_account_from_stripe_data(stripe_account)


def sync_account_from_stripe_data(data, user=None):
    """
    Create or update using the account object from a Stripe API query.

    Args:
        data: the data representing an account object in the Stripe API

    Returns:
        a pinax.stripe.models.Account object
    """
    kwargs = {"stripe_id": data["id"]}
    if user:
        kwargs["user"] = user
    obj, created = models.Account.objects.get_or_create(
        **kwargs
    )
    common_attrs = (
        "business_name", "business_url", "charges_enabled", "country",
        "default_currency", "details_submitted", "display_name",
        "email", "type", "statement_descriptor", "support_email",
        "support_phone", "timezone", "payouts_enabled"
    )

    custom_attrs = (
        "debit_negative_balances", "metadata", "product_description",
        "payout_statement_descriptor"
    )

    if data["type"] == "custom":
        top_level_attrs = common_attrs + custom_attrs
    else:
        top_level_attrs = common_attrs

    for a in [x for x in top_level_attrs if x in data]:
        setattr(obj, a, data[a])

    # that's all we get for standard and express accounts!
    if data["type"] != "custom":
        obj.save()
        return obj

    # otherwise we continue on to gather a range of details available
    # to us on custom accounts

    # legal entity for individual accounts
    le = data["legal_entity"]
    address = le["address"]
    obj.legal_entity_address_city = address["city"]
    obj.legal_entity_address_country = address["country"]
    obj.legal_entity_address_line1 = address["line1"]
    obj.legal_entity_address_line2 = address["line2"]
    obj.legal_entity_address_postal_code = address["postal_code"]
    obj.legal_entity_address_state = address["state"]

    dob = le["dob"]
    if dob:
        obj.legal_entity_dob = datetime.date(
            dob["year"], dob["month"], dob["day"]
        )
    else:
        obj.legal_entity_dob = None

    obj.legal_entity_type = le["type"]
    obj.legal_entity_first_name = le["first_name"]
    obj.legal_entity_last_name = le["last_name"]
    obj.legal_entity_personal_id_number_provided = le["personal_id_number_provided"]

    # these attributes are not always present
    obj.legal_entity_gender = le.get(
        "gender", obj.legal_entity_gender
    )
    obj.legal_entity_maiden_name = le.get(
        "maiden_name", obj.legal_entity_maiden_name
    )
    obj.legal_entity_phone_number = le.get(
        "phone_number", obj.legal_entity_phone_number
    )
    obj.legal_entity_ssn_last_4_provided = le.get(
        "ssn_last_4_provided", obj.legal_entity_ssn_last_4_provided
    )

    verification = le["verification"]
    if verification:
        obj.legal_entity_verification_details = verification.get("details")
        obj.legal_entity_verification_details_code = verification.get("details_code")
        obj.legal_entity_verification_document = verification.get("document")
        obj.legal_entity_verification_status = verification.get("status")
    else:
        obj.legal_entity_verification_details = None
        obj.legal_entity_verification_details_code = None
        obj.legal_entity_verification_document = None
        obj.legal_entity_verification_status = None

    # tos state
    if data["tos_acceptance"]["date"]:
        obj.tos_acceptance_date = datetime.datetime.utcfromtimestamp(
            data["tos_acceptance"]["date"]
        )
    else:
        obj.tos_acceptance_date = None
    obj.tos_acceptance_ip = data["tos_acceptance"]["ip"]
    obj.tos_acceptance_user_agent = data["tos_acceptance"]["user_agent"]

    # decline charge on certain conditions
    obj.decline_charge_on_avs_failure = data["decline_charge_on"]["avs_failure"]
    obj.decline_charge_on_cvc_failure = data["decline_charge_on"]["cvc_failure"]

    # transfer schedule to external account
    ps = data["payout_schedule"]
    obj.payout_schedule_interval = ps["interval"]
    obj.payout_schedule_delay_days = ps.get("delay_days")
    obj.payout_schedule_weekly_anchor = ps.get("weekly_anchor")
    obj.payout_schedule_monthly_anchor = ps.get("monthly_anchor")

    # verification status, key to progressing account setup
    obj.verification_disabled_reason = data["verification"]["disabled_reason"]
    obj.verification_due_by = utils.convert_tstamp(data["verification"], "due_by")
    obj.verification_fields_needed = data["verification"]["fields_needed"]

    obj.save()

    # sync any external accounts (bank accounts only for now) included
    for external_account in data["external_accounts"]["data"]:
        if external_account["object"] == "bank_account":
            sync_bank_account_from_stripe_data(external_account)

    return obj


def delete(account):
    """
    Delete an account both remotely and locally.

    Note that this will fail if the account's balance is
    non-zero.
    """
    account.stripe_account.delete()
    account.delete()


def deauthorize(account):
    account.authorized = False
    account.save()
