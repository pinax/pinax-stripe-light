from django import forms

from payments.settings import PLAN_CHOICES

sorted_plan_choices = sorted(PLAN_CHOICES)

class PlanForm(forms.Form):
    # pylint: disable=R0924
    plan = forms.ChoiceField(choices= sorted_plan_choices + [("", "-------")])
