from django import forms

from payments.settings import PLAN_CHOICES


class PlanForm(forms.Form):
    
    plan = forms.ChoiceField(choices=PLAN_CHOICES + [("", "-------")])
