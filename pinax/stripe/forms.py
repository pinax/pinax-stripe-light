from django import forms

from .models import Plan


class PlanForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all())
