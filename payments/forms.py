from django import forms

from payments.settings import PLAN_CHOICES
sorted_plan_choices = sorted(PLAN_CHOICES)

class PlanForm(forms.Form):
    
    plan = forms.ChoiceField(choices=sorted_plan_choices + [("", "-------")])
