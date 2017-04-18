from django import forms
from django.utils.translation import ugettext_lazy as _

from .conf import settings
from .models import Plan
import datetime


STRIPE_MINIMUM_DOB = datetime.date(1900, 1, 1)


class PaymentMethodForm(forms.Form):

    expMonth = forms.IntegerField(min_value=1, max_value=12)
    expYear = forms.IntegerField(min_value=2015, max_value=9999)


class PlanForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all())


"""
The Connect forms here are designed to get users through the multi-stage
verification process Stripe uses for managed accounts, as detailed here:

https://stripe.com/docs/connect/testing-verification

You can view the required fields on a per-country basis using the API:

https://stripe.com/docs/api#country_spec_object

The following forms are sufficient for the US and Canada.
"""


class BaseIndividualManagedAccountForm(forms.Form):

    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    dob = forms.DateField()

    address_line1 = forms.CharField(max_length=300)
    address_city = forms.CharField(max_length=100)
    address_state = forms.CharField(max_length=100)
    address_country = forms.CharField(max_length=2)
    address_postal_code = forms.CharField(max_length=100)

    # for external_account
    routing_number = forms.CharField(max_length=100)
    account_number = forms.CharField(max_length=100)
    currency = forms.CharField(max_length=3)

    tos_accepted = forms.BooleanField()

    def clean_dob(self):
        data = self.cleaned_data['dob']
        if data < STRIPE_MINIMUM_DOB:
            raise forms.ValidationError(
                'This must be greater than {}.'.format(
                    STRIPE_MINIMUM_DOB
                )
            )
        return data


class Phase2ManagedAccountForm(BaseIndividualManagedAccountForm):
    """
    Collect `minimum` fields for CA and US CountrySpecs.

    Note: for US, `legal_entity.ssn_last_4` appears in the `minimum`
    set but in fact is not required for the account to be functional.
    Similarly for CA, `legal_entity.personal_id_number` is listed as
    `minimum` but in practice is not required to be able to charge
    and transfer.
    """


class Phase4ManagedAccountForm(BaseIndividualManagedAccountForm):
    """Collect `additional` fields for CA and US CountrySpecs."""

    personal_id_number = forms.CharField(max_length=100)
    document = forms.BooleanField()

    accepted_content_types = set((
        'image/jpg', 'image/jpeg', 'image/png'
    ))

    def clean_document(self):
        document = self.cleaned_data.get('document')
        if document._size > settings.DOCUMENT_MAX_SIZE_KB:
            raise forms.ValidationError(
                _('Document image is too large (> %(maxsize)sMB)') % {
                    'maxsize': settings.DOCUMENT_MAX_SIZE_KB / (1024 * 1024)
                }
            )
        if document.content_type not in self.accepted_content_types:
            raise forms.ValidationError(
                _(
                    'The type of image you supplied is not supported. '
                    'Please upload a JPG or PNG file.'
                )
            )
        return document
