from django import template

from django.conf import settings

from payments.forms import CardTokenForm, ChangePlanForm, SubscribeForm


register = template.Library()


@register.inclusion_tag("payments/_change_plan_form.html", takes_context=True)
def change_plan_form(context):
    context.update({
        "form": ChangePlanForm(initial={
            "plan": context["request"].user.customer.plan
        })
    })
    return context


@register.inclusion_tag("payments/_change_plan_form.html", takes_context=True)
def change_card_form(context):
    context.update({
        "form": CardTokenForm()
    })
    return context


@register.inclusion_tag("payments/_subscribe_form.html", takes_context=True)
def subscribe_form(context):
    context.update({
        "form": SubscribeForm(),
        "plans": settings.PAYMENTS_PLANS,
    })
    return context
