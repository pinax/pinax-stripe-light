from django import forms

from .proxies import PlanProxy


class PlanForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=PlanProxy.objects.all)
