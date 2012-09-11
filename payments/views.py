import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.contrib.auth.decorators import login_required

import stripe

from payments.forms import PlanForm
from payments.models import Event, EventProcessingException


def _ajax_response(request, template, **kwargs):
    if request.is_ajax:
        response = {
            "html": render_to_string(
                template,
                RequestContext(request, kwargs)
            )
        }
        if "location" in kwargs:
            response.update({"location": kwargs["location"]})
        return HttpResponse(json.dumps(response), mimetype="application/json")


@require_POST
@login_required
def change_card(request):
    if request.POST.get("stripe_token"):
        try:
            request.user.customer.update_card(request.POST.get("stripe_token"))
            data = {}
        except stripe.CardError, e:
            data = {"error": e.message}
    return _ajax_response(request, "payments/_change_card_form.html", **data)


@require_POST
@login_required
def change_plan(request):
    form = PlanForm(request.POST)
    if form.is_valid():
        try:
            request.user.customer.purchase(form.cleaned_data["plan"])
            data = {
                "form": PlanForm(initial={
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
                "form": PlanForm(initial={
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
def subscribe(request, form_class=PlanForm):
    data = {"plans": settings.PAYMENTS_PLANS}
    form = form_class(request.POST)
    if form.is_valid():
        try:
            customer = request.user.customer
            customer.update_card(request.POST.get("stripe_token"))
            customer.purchase(form.cleaned_data["plan"])
            data["form"] = form_class()
            data["location"] = reverse("payments_history")
        except stripe.StripeError, e:
            data["form"] = form
            data["error"] = e.message
    else:
        data["error"] = form.errors
        data["form"] = form
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
    if Event.objects.filter(stripe_id=data["id"]).exists():
        EventProcessingException.objects.create(
            data=data,
            message="Duplicate event record",
            traceback=""
        )
    else:
        event = Event.objects.create(
            stripe_id=data["id"],
            kind=data["type"],
            livemode=data["livemode"],
            webhook_message=data
        )
        event.validate()
        event.process()
    return HttpResponse()
