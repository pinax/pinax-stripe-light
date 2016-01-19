from django import forms

from .models import Plan


class PaymentMethodForm(forms.Form):

    expMonth = forms.IntegerField(min_value=1, max_value=12)
    expYear = forms.IntegerField(min_value=2015, max_value=9999)


class PlanForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all())
