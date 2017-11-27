import datetime
import time

from django import forms
from django.utils.translation import ugettext_lazy as _

import stripe
from ipware.ip import get_ip, get_real_ip

from .actions import accounts
from .conf import settings
from .models import Plan


class PaymentMethodForm(forms.Form):

    expMonth = forms.IntegerField(min_value=1, max_value=12)
    expYear = forms.IntegerField(min_value=2015, max_value=9999)


class PlanForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all())


"""
The Connect forms here are designed to get users through the multi-stage
verification process Stripe uses for custom accounts, as detailed here:

https://stripe.com/docs/connect/testing-verification

You can view the required fields on a per-country basis using the API:

https://stripe.com/docs/api#country_spec_object

The following forms are sufficient for the US and Canada.
"""

# Note: undocumented, determined through experimentation
STRIPE_MINIMUM_DOB = datetime.date(1900, 1, 1)


ACCEPTED_DOCUMENT_CONTENT_TYPES = (
    "image/jpg", "image/jpeg", "image/png"
)

COUNTRY_CHOICES = [
    ("CA", _("Canada")),
    ("US", _("United States"))
]

STATE_CHOICES_BY_COUNTRY = {
    "CA": [
        ("AB", _("Alberta")),
        ("BC", _("British Columbia")),
        ("MB", _("Manitoba")),
        ("NB", _("New Brunswick")),
        ("NL", _("Newfoundland and Labrador")),
        ("NT", _("Northwest Territories")),
        ("NS", _("Nova Scotia")),
        ("NU", _("Nunavut")),
        ("ON", _("Ontario")),
        ("PE", _("Prince Edward Island")),
        ("QC", _("Quebec")),
        ("SK", _("Saskatchewan")),
        ("YT", _("Yukon"))
    ],
    "US": [
        ("AL", _("Alabama")),
        ("AK", _("Alaska")),
        ("AZ", _("Arizona")),
        ("AR", _("Arkansas")),
        ("CA", _("California")),
        ("CO", _("Colorado")),
        ("CT", _("Connecticut")),
        ("DE", _("Delaware")),
        ("DC", _("District of Columbia")),
        ("FL", _("Florida")),
        ("GA", _("Georgia")),
        ("HI", _("Hawaii")),
        ("ID", _("Idaho")),
        ("IL", _("Illinois")),
        ("IN", _("Indiana")),
        ("IA", _("Iowa")),
        ("KS", _("Kansas")),
        ("KY", _("Kentucky")),
        ("LA", _("Louisiana")),
        ("ME", _("Maine")),
        ("MD", _("Maryland")),
        ("MA", _("Massachusetts")),
        ("MI", _("Michigan")),
        ("MN", _("Minnesota")),
        ("MS", _("Mississippi")),
        ("MO", _("Missouri")),
        ("MT", _("Montana")),
        ("NE", _("Nebraska")),
        ("NV", _("Nevada")),
        ("NH", _("New Hampshire")),
        ("NJ", _("New Jersey")),
        ("NM", _("New Mexico")),
        ("NY", _("New York")),
        ("NC", _("North Carolina")),
        ("ND", _("North Dakota")),
        ("OH", _("Ohio")),
        ("OK", _("Oklahoma")),
        ("OR", _("Oregon")),
        ("PA", _("Pennsylvania")),
        ("RI", _("Rhode Island")),
        ("SC", _("South Carolina")),
        ("SD", _("South Dakota")),
        ("TN", _("Tennessee")),
        ("TX", _("Texas")),
        ("UT", _("Utah")),
        ("VT", _("Vermont")),
        ("VA", _("Virginia")),
        ("WA", _("Washington")),
        ("WV", _("West Virginia")),
        ("WI", _("Wisconsin")),
        ("WY", _("Wyoming"))
    ]
}

CURRENCY_CHOICES_BY_COUNTRY = {
    "CA": [
        ("CAD", _("CAD: Canadian Dollars")),
        ("USD", _("USD: US Dollars")),
    ],
    "US": [
        ("USD", _("USD: US Dollars")),
    ]
}

FIELDS_BY_COUNTRY = {
    "CA": {
        "legal_entity.personal_id_number": (
            "personal_id_number",
            forms.CharField(
                label=_("SIN")
            ),
        ),
        "legal_entity.verification.document": (
            "document",
            forms.FileField(
                label=_("Scan of government-issued ID")
            ),
        )
    },
    "US": {
        "legal_entity.personal_id_number": (
            "personal_id_number",
            forms.CharField(
                label=_("SSN")
            )
        ),
        "legal_entity.verification.document": (
            "document",
            forms.FileField(
                label=_("Scan of government-issued ID")
            ),
        )
    }
}

# lookup local form fields for Stripe field errors
# we use `contains` so the stripe side (left) need
# not be super specific

STRIPE_FIELDS_TO_LOCAL_FIELDS = {
    "dob": "dob",
    "first_name": "first_name",
    "second_name": "second_name",
    "routing_number": "routing_number",
    "currency": "currency",
    "account_number": "account_number",
    "personal_id_number": "personal_id_number",
    "file": "document"
}


class DynamicManagedAccountForm(forms.Form):
    """Set up fields according to fields needed and relevant country."""

    def __init__(self, *args, **kwargs):
        self.country = kwargs.pop("country")
        self.fields_needed = kwargs.pop("fields_needed", [])
        super(DynamicManagedAccountForm, self).__init__(*args, **kwargs)
        # build our form using the country specific fields and falling
        # back to our default set
        for f in self.fields_needed:
            if f in FIELDS_BY_COUNTRY.get(self.country, {}):  # pragma: no branch
                field_name, field = FIELDS_BY_COUNTRY[self.country][f]
                self.fields[field_name] = field

    # clean methods only kick in if the form has the relevant field

    def clean_document(self):
        document = self.cleaned_data.get("document")
        if document._size > settings.PINAX_STRIPE_DOCUMENT_MAX_SIZE_KB:
            raise forms.ValidationError(
                _("Document image is too large (> %(maxsize)s MB)") % {
                    "maxsize": round(
                        float(
                            settings.PINAX_STRIPE_DOCUMENT_MAX_SIZE_KB
                        ) / float(
                            1024 * 1024
                        ), 1
                    )
                }
            )
        if document.content_type not in ACCEPTED_DOCUMENT_CONTENT_TYPES:
            raise forms.ValidationError(
                _(
                    "The type of image you supplied is not supported. "
                    "Please upload a JPG or PNG file."
                )
            )
        return document

    def clean_dob(self):
        data = self.cleaned_data["dob"]
        if data < STRIPE_MINIMUM_DOB:
            raise forms.ValidationError(
                "This must be greater than {}.".format(
                    STRIPE_MINIMUM_DOB
                )
            )
        return data

    def stripe_field_to_local_field(self, stripe_field):
        for r, l in STRIPE_FIELDS_TO_LOCAL_FIELDS.items():
            if r in stripe_field:
                return l

    def stripe_error_to_form_error(self, error):
        """
        Translate a Stripe error into meaningful form feedback.

        error.json_body = {
            u'error': {
                u'message':
                u"This value must be greater than 1900.",
                u'type': u'invalid_request_error',
                u'param': u'legal_entity[dob][year]'
            }
        }
        """
        message = error.json_body["error"]["message"]
        stripe_field = error.json_body["error"]["param"]
        local_field = self.stripe_field_to_local_field(stripe_field)
        if local_field:
            self.add_error(local_field, message)
        else:
            self.add_error(None, message)


def extract_ipaddress(request):
    """Extract IP address from request."""
    ipaddress = get_real_ip(request)
    if not ipaddress and settings.DEBUG:  # pragma: no cover
        ipaddress = get_ip(request)
    return ipaddress


class InitialCustomAccountForm(DynamicManagedAccountForm):
    """
    Collect `minimum` fields for CA and US CountrySpecs.

    Note: for US, `legal_entity.ssn_last_4` appears in the `minimum`
    set but in fact is not required for the account to be functional.
    Similarly for CA, `legal_entity.personal_id_number` is listed as
    `minimum` but in practice is not required to be able to charge
    and transfer.
    """

    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    dob = forms.DateField()

    address_line1 = forms.CharField(max_length=300)
    address_city = forms.CharField(max_length=100)
    address_state = forms.CharField(max_length=100)
    address_country = forms.ChoiceField(choices=COUNTRY_CHOICES)
    address_postal_code = forms.CharField(max_length=100)

    # for external_account
    routing_number = forms.CharField(max_length=100)
    account_number = forms.CharField(max_length=100)

    tos_accepted = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        """Instantiate no fields based on `fields_needed` initially."""
        self.request = kwargs.pop("request")
        super(InitialCustomAccountForm, self).__init__(
            *args, **kwargs
        )
        self.fields["address_state"] = forms.ChoiceField(
            choices=STATE_CHOICES_BY_COUNTRY[self.country]
        )
        self.fields["currency"] = forms.ChoiceField(
            choices=CURRENCY_CHOICES_BY_COUNTRY[self.country]
        )

    def get_ipaddress(self):
        return extract_ipaddress(self.request)

    def get_user_agent(self):
        return self.request.META.get("HTTP_USER_AGENT")

    def save(self):
        """
        Create a custom account, handling Stripe errors.

        Note: the below will create a custom, manually paid out
        account. This is here mostly as an example, you will likely
        need to override this method and do your own application
        specific special sauce.
        """
        data = self.cleaned_data
        try:
            return accounts.create(
                self.request.user,
                country=data["address_country"],
                type="custom",
                legal_entity={
                    "dob": {
                        "day": data["dob"].day,
                        "month": data["dob"].month,
                        "year": data["dob"].year
                    },
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "type": "individual",
                    "address": {
                        "line1": data["address_line1"],
                        "city": data["address_city"],
                        "postal_code": data["address_postal_code"],
                        "state": data["address_state"],
                        "country": data["address_country"]
                    }
                },
                tos_acceptance={
                    "date": int(time.time()),
                    "ip": self.get_ipaddress(),
                    "user_agent": self.get_user_agent()
                },
                transfer_schedule={
                    "interval": "manual"
                },
                external_account={
                    "object": "bank_account",
                    "account_holder_name": u" ".join(
                        [
                            data["first_name"],
                            data["last_name"]
                        ]
                    ),
                    "country": data["address_country"],
                    "currency": data["currency"],
                    "account_holder_type": "individual",
                    "default_for_currency": True,
                    "account_number": data["account_number"],
                    "routing_number": data["routing_number"]
                },
                # useful reference to our local user instance
                metadata={
                    "user_id": self.request.user.id
                }
            )

        except stripe.error.InvalidRequestError as se:
            self.stripe_error_to_form_error(se)
            raise


class AdditionalCustomAccountForm(DynamicManagedAccountForm):
    """
    Collect `additional` fields for CA and US CountrySpecs.

    Note: for US, `legal_entity.ssn_last_4` appears in the `minimum`
    set but in fact is not required for the account to be functional.
    Similarly for CA, `legal_entity.personal_id_number` is listed as
    `minimum` but in practice is not required to be able to charge
    and transfer.

    It's possible when further verification is needed that the user
    made a mistake with their name or dob, so we include these
    fields so the user can make any adjustments.
    """

    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    dob = forms.DateField()

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop("account")
        kwargs.update(
            {
                "country": self.account.country,
                "fields_needed": self.account.verification_fields_needed,
            }
        )
        super(AdditionalCustomAccountForm, self).__init__(*args, **kwargs)
        # prepopulate with the existing account details
        self.fields["first_name"].initial = self.account.legal_entity_first_name
        self.fields["last_name"].initial = self.account.legal_entity_last_name
        self.fields["dob"].initial = self.account.legal_entity_dob

    def save(self):
        data = self.cleaned_data
        try:
            return accounts.update(
                self.account,
                {
                    "dob": {
                        "day": data["dob"].day,
                        "month": data["dob"].month,
                        "year": data["dob"].year
                    },
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "personal_id_number": data.get("personal_id_number"),
                    "document": data.get("document")
                }
            )
        except stripe.error.InvalidRequestError as se:
            self.stripe_error_to_form_error(se)
            raise
