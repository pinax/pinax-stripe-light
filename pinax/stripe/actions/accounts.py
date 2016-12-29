import stripe

from .. import models
import datetime


def create(user, country, managed=True, individual=True):
    """
    Create an Account.

    Args:
        country: two letter country code for where the individual lives
        managed: boolean field dictating whether we collect details from the user, or Stripe does

    Returns:
        a pinax.stripe.models.Account object
    """
    stripe_account = stripe.Account.create(
        country=country,
        managed=managed,
        type='individual' if individual else 'corporation'
    )
    return sync_account_from_stripe_data(stripe_account, user=user)


def sync_account_from_stripe_data(data, user=None):
    """
    Create or update using the account object from a Stripe API query.

    Args:
        data: the data representing an account object in the Stripe API

    Returns:
        a pinax.stripe.models.Account object
    """
    kwargs = {'stripe_id': data['id']}
    if user:
        kwargs['user'] = user
    obj, created = models.Account.objects.get_or_create(
        **kwargs
    )
    top_level_attrs = (
        'business_name', 'business_url', 'charges_enabled', 'country',
        'debit_negative_balances', 'default_currency', 'details_submitted',
        'display_name', 'email', 'managed', 'metadata', 'product_description',
        'statement_descriptor', 'support_email', 'support_phone',
        'timezone', 'transfer_statement_descriptor', 'transfers_enabled'
    )
    for a in top_level_attrs:
        setattr(obj, a, data.get(a))

    # legal entity for individual accounts
    le = data['legal_entity']
    address = le['address']
    obj.legal_entity_address_city = address['city']
    obj.legal_entity_address_country = address['country']
    obj.legal_entity_address_line1 = address['line1']
    obj.legal_entity_address_line2 = address['line2']
    obj.legal_entity_address_postal_code = address['postal_code']
    obj.legal_entity_address_state = address['state']

    dob = le['dob']
    if dob:
        obj.legal_entity_dob = datetime.date(
            dob['year'], dob['month'], dob['day']
        )
    else:
        obj.legal_entity_dob = None

    obj.legal_entity_first_name = le['first_name']
    obj.legal_entity_last_name = le['last_name']
    obj.legal_entity_gender = le['gender']
    obj.legal_entity_maiden_name = le['maiden_name']
    obj.legal_entity_personal_id_number_provided = le['personal_id_number_provided']
    obj.legal_entity_phone_number = le['phone_number']
    obj.legal_entity_ssn_last_4_provided = le['ssn_last_4_provided']
    obj.legal_entity_type = le['type']

    verification = le['verification']
    if verification:
        obj.legal_entity_verification_details = verification.get('details')
        obj.legal_entity_verification_details_code = verification.get('details_code')
        obj.legal_entity_verification_document = verification.get('document')
        obj.legal_entity_verification_status = verification.get('status')
    else:
        obj.legal_entity_verification_details = None
        obj.legal_entity_verification_details_code = None
        obj.legal_entity_verification_document = None
        obj.legal_entity_verification_status = None

    # tos state
    if data['tos_acceptance']['date']:
        obj.tos_acceptance_date = datetime.datetime.utcfromtimestamp(
            data['tos_acceptance']['date']
        )
    else:
        obj.tos_acceptance_date = None
    obj.tos_acceptance_ip = data['tos_acceptance']['ip']
    obj.tos_acceptance_user_agent = data['tos_acceptance']['user_agent']

    # decline charge on certain conditions
    obj.decline_charge_on_avs_failure = data['decline_charge_on']['avs_failure']
    obj.decline_charge_on_cvc_failure = data['decline_charge_on']['cvc_failure']

    # transfer schedule to external account
    ts = data['transfer_schedule']
    obj.transfer_schedule_interval = ts['interval']
    obj.transfer_schedule_delay_days = ts.get('delay_days')
    obj.transfer_schedule_weekly_anchor = ts.get('weekly_anchor')
    obj.transfer_schedule_monthly_anchor = ts.get('monthly_anchor')

    # verification status, key to progressing account setup
    obj.verification_disabled_reason = data['verification']['disabled_reason']
    obj.verification_due_by = data['verification']['due_by']
    obj.verification_fields_needed = data['verification']['fields_needed']

    obj.save()
    return obj
