from django import forms

from .settings import PLAN_CHOICES

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Column, Div, Field, Fieldset, ButtonHolder, Submit


class PlanForm(forms.Form):
    # pylint: disable=R0924

    plan = forms.ChoiceField(choices=PLAN_CHOICES + [("", "-------")], label="Plan")
    coupon = forms.CharField(label="Coupon Code", required=False)

    def __init__(self, *args, **kwargs):
        super(PlanForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Field('plan'),
                    css_class='col-md-3 col-md-offset-2'
                ),
                Div(
                    Field('coupon'),
                    css_class='col-md-3 col-md-offset-2'
                ),
                css_class='row',
            ),
            ButtonHolder(
                Submit('submit', 'Submit', css_class='button white')
            )
        )
