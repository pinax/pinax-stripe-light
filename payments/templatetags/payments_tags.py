from django import template

from ..forms import PlanForm


register = template.Library()


@register.inclusion_tag("payments/_change_plan_form.html", takes_context=True)
def change_plan_form(context):
    context.update({
        "form": PlanForm(initial={
            "plan": context["request"].user.customer.current_subscription.plan
        })
    })
    return context


@register.inclusion_tag("payments/_subscribe_form.html", takes_context=True)
def subscribe_form(context):
    context.update({
        "form": PlanForm()
    })
    return context
