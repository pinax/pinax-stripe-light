from django import forms

from .settings import PLAN_CHOICES


class PlanForm(forms.Form):
    # pylint: disable-msg=R0924
    plan = forms.ChoiceField(choices=PLAN_CHOICES + [("", "-------")])
