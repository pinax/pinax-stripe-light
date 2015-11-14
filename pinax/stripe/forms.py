from django import forms

from .conf import settings


PLAN_CHOICES = [
    (plan, settings.PINAX_STRIPE_PLANS[plan].get("name", plan))
    for plan in settings.PINAX_STRIPE_PLANS
]


class PlanForm(forms.Form):
    plan = forms.ChoiceField(choices=PLAN_CHOICES + [("", "-------")])
