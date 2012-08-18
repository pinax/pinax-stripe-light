from django import forms

from payments.models import PLAN_CHOICES


class CardTokenForm(forms.Form):
    
    def save(self, user):
        user.customer.update_card(self.cleaned_data["token"])


class ChangePlanForm(forms.Form):
    
    plan = forms.ChoiceField(choices=PLAN_CHOICES)
    
    def save(self, user):
        user.customer.purchase(self.cleaned_data["plan"])


class SubscribeForm(CardTokenForm, ChangePlanForm):
    
    def save(self, user):
        user.customer.update_card(self.cleaned_data["token"])
        user.customer.purchase(self.cleaned_data["plan"])
