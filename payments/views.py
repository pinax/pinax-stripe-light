import json

from django.conf import settings
from django.http import HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.contrib.auth.decorators import login_required

import stripe

from payments.forms import CardTokenForm, SubscribeForm, ChangePlanForm
from payments.models import Event


def _ajax_response(request, template, **kwargs):
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
    form = CardTokenForm(request.POST)
    if form.is_valid():
        try:
            form.save(user=request.user)
            data = {
                "form": CardTokenForm(),
                "last4": request.user.customer.card_last_4,
                "kind": request.user.customer.card_kind
            }
        except stripe.CardError, e:
            data = {"error": e, "form": form}
    return _ajax_response("payments/_change_card_form.html", **data)


@require_POST
@login_required
def change_plan(request):
    form = ChangePlanForm(request.POST)
    if form.is_valid():
        form.save(user=request.user)
        data = {
            "form": ChangePlanForm(initial={
                "plan": request.user.customer.plan
            }),
            "plan": request.user.customer.plan,
            "name": settings.PAYMENTS_PLANS[request.user.customer.plan]["name"]
        }
    else:
        data = {
            "form": form
        }
    return _ajax_response("payments/_change_plan_form.html", **data)


@require_POST
@login_required
def subscribe(request):
    data = {"plans": settings.PAYMENTS_PLANS}
    form = SubscribeForm(request.POST)
    if form.is_valid():
        try:
            form.save(user=request.user)
            data["form"] = SubscribeForm()
        except stripe.CardError, e:
            data["form"] = form
            data["error"] = e
    return _ajax_response("payments/_subscribe_form.html", **data)


@require_POST
@login_required
def cancel_subscription(request):
    request.user.customer.cancel()
    data = {}
    return _ajax_response("payments/_cancel-form.html", **data)


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
