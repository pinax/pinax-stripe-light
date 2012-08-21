import json

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.contrib.auth.decorators import login_required

import stripe

from payments.forms import SubscribeForm, ChangePlanForm
from payments.models import Event


def _ajax_response(request, template, **kwargs):
    if request.is_ajax:
        response = {
            "html": render_to_string(
                template,
                RequestContext(request, kwargs)
            )
        }
        return HttpResponse(json.dumps(response), mimetype="application/json")


@require_POST
@login_required
def change_card(request):
    if request.POST.get("stripe_token"):
        try:
            request.user.customer.update_card(request.POST.get("stripe_token"))
            return redirect("payments_change_card")
        except stripe.CardError, e:
            data = {"error": e.message}
    return _ajax_response(request, "payments/_change_card_form.html", **data)


@require_POST
@login_required
def change_plan(request):
    form = ChangePlanForm(request.POST)
    if form.is_valid():
        try:
            form.save(user=request.user)
            data = {
                "form": ChangePlanForm(initial={
                    "plan": request.user.customer.plan
                }),
                "plan": request.user.customer.plan,
                "name": settings.PAYMENTS_PLANS[request.user.customer.plan]["name"]
            }
        except stripe.StripeError, e:
            if request.user.customer.plan:
                name = settings.PAYMENTS_PLANS[request.user.customer.plan]["name"]
            else:
                name = ""
            data = {
                "form": ChangePlanForm(initial={
                    "plan": request.user.customer.plan
                }),
                "plan": request.user.customer.plan,
                "name": name,
                "error": e.message
            }
    else:
        data = {
            "form": form
        }
    return _ajax_response(request, "payments/_change_plan_form.html", **data)


@require_POST
@login_required
def subscribe(request):
    data = {"plans": settings.PAYMENTS_PLANS}
    form = SubscribeForm(request.POST)
    if form.is_valid():
        try:
            form.save(user=request.user)
            data["form"] = SubscribeForm()
        except stripe.StripeError, e:
            data["form"] = form
            data["error"] = e.message
    return _ajax_response(request, "payments/_subscribe_form.html", **data)


@require_POST
@login_required
def cancel(request):
    try:
        request.user.customer.cancel()
        data = {}
    except stripe.StripeError, e:
        data = {"error": e.message}
    return _ajax_response(request, "payments/_cancel_form.html", **data)


@csrf_exempt
@require_POST
def webhook(request):
    data = json.loads(request.raw_post_data)
    event = Event.objects.create(
        stripe_id=data["id"],
        kind=data["type"],
        livemode=data["livemode"],
        webhook_message=data
    )
    event.validate()
    event.process()
    return HttpResponse()
