from django import forms

from payments.settings import PLAN_CHOICES


class ChangePlanForm(forms.Form):
    
    plan = forms.ChoiceField(choices=PLAN_CHOICES)
    
    def save(self, user):
        user.customer.purchase(self.cleaned_data["plan"])


class SubscribeForm(ChangePlanForm):
    
    def save(self, user):
        user.customer.update_card(self.cleaned_data["stripe_token"])
        user.customer.purchase(self.cleaned_data["plan"])
