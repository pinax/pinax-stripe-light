from django import forms

from .models import Plan


class PaymentMethodForm(forms.Form):

    expMonth = forms.IntegerField(min_value=1, max_value=12)
    expYear = forms.IntegerField(min_value=2015, max_value=9999)


class PlanForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all())


class ManagedAccountForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    dob = forms.DateField()

    address_line_1 = forms.CharField(max_length=300)
    address_city = forms.CharField(max_length=100)
    address_state = forms.CharField(max_length=100)
    address_country = forms.CharField(max_length=2)
    address_postal_code = forms.CharField(max_length=100)
    ssn_last4 = forms.CharField(max_length=100)
    routing_number = forms.CharField(max_length=100)
    account_number = forms.CharField(max_length=100)

    tos_accepted = forms.BooleanField()

    # "external_account",
    # "legal_entity.dob.day",
    # "legal_entity.dob.month",
    # "legal_entity.dob.year",
    # "legal_entity.first_name",
    # "legal_entity.last_name",
    # "legal_entity.type",
    # "tos_acceptance.date",
    # "tos_acceptance.ip"
