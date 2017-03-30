from django import forms

from .models import Plan
import datetime


STRIPE_MINIMUM_DOB = datetime.date(1900, 1, 1)


class PaymentMethodForm(forms.Form):

    expMonth = forms.IntegerField(min_value=1, max_value=12)
    expYear = forms.IntegerField(min_value=2015, max_value=9999)


class PlanForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all())


class ManagedAccountForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    dob = forms.DateField()

    address_line1 = forms.CharField(max_length=300)
    address_city = forms.CharField(max_length=100)
    address_state = forms.CharField(max_length=100)
    address_country = forms.CharField(max_length=2)
    address_postal_code = forms.CharField(max_length=100)

    #personal_id_number = forms.CharField(max_length=100)
    routing_number = forms.CharField(max_length=100)
    account_number = forms.CharField(max_length=100)
    currency = forms.CharField(initial='CAD', max_length=3)

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
