import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_str
from django.views.generic import TemplateView, View
from django.views.decorators.csrf import csrf_exempt

import stripe

from eldarion.ajax.views import EldarionAjaxResponseMixin

from .conf import settings
from .forms import PlanForm, PLAN_CHOICES
from .models import (
    Customer,
    CurrentSubscription,
    Event,
    EventProcessingException
)


class PaymentsContextMixin(object):

    def get_context_data(self, **kwargs):
        context = super(PaymentsContextMixin, self).get_context_data(**kwargs)
        context.update({
            "STRIPE_PUBLIC_KEY": settings.PINAX_STRIPE_PUBLIC_KEY,
            "PLAN_CHOICES": PLAN_CHOICES,
            "PAYMENT_PLANS": settings.PINAX_STRIPE_PLANS
        })
        return context


def _ajax_response(request, template, **kwargs):
    response = {
        "html": render_to_string(
            template,
            RequestContext(request, kwargs)
        )
    }
    if "location" in kwargs:
        response.update({"location": kwargs["location"]})
    return HttpResponse(json.dumps(response), content_type="application/json")


class SubscribeView(PaymentsContextMixin, TemplateView):
    template_name = "payments/subscribe.html"

    def get_context_data(self, **kwargs):
        context = super(SubscribeView, self).get_context_data(**kwargs)
        context.update({
            "form": PlanForm
        })
        return context


class ChangeCardView(PaymentsContextMixin, TemplateView):
    template_name = "payments/change_card.html"


class CancelView(PaymentsContextMixin, TemplateView):
    template_name = "payments/cancel.html"


class ChangePlanView(SubscribeView):
    template_name = "payments/change_plan.html"


class HistoryView(PaymentsContextMixin, TemplateView):
    template_name = "payments/history.html"


class CustomerMixin(object):

    @property
    def customer(self):
        if not hasattr(self, "_customer"):
            self._customer = self.request.user.customer
        return self._customer


class AjaxChangeCard(EldarionAjaxResponseMixin, CustomerMixin, View):

    template_fragment = "payments/_change_card_form.html"

    def send_invoice(self):
        if self.customer.card_fingerprint == "":
            self.customer.send_invoice()

    def update_card(self, stripe_token):
        self.customer.update_card(stripe_token)

    def retry_unpaid_invoices(self):
        self.customer.retry_unpaid_invoices()

    def post(self, request, *args, **kwargs):
        try:
            self.update_card(request.POST.get("stripe_token"))
            self.send_invoice()
            self.retry_unpaid_invoices()
            data = {}
        except stripe.CardError as e:
            data = {"error": smart_str(e)}
        return self.render_to_response(data)


class AjaxChangePlan(EldarionAjaxResponseMixin, CustomerMixin, View):

    form_class = PlanForm
    template_fragment = "payments/_change_plan_form.html"

    @property
    def current_plan(self):
        if not hasattr(self, "_current_plan"):
            sub = next(iter(CurrentSubscription.objects.filter(customer=self.customer)), None)
            if sub:
                self._current_plan = sub.plan
        return self._current_plan

    def subscribe(self, plan):
        try:
            self.customer.subscribe(plan)
            data = {
                "form": PlanForm(initial={"plan": plan})
            }
        except stripe.StripeError as e:
            data = {
                "form": PlanForm(initial={"plan": self.current_plan}),
                "error": smart_str(e)
            }
        return data

    def form_valid(self, form):
        data = self.subscribe(plan=form.cleaned_data["plan"])
        return self.render_to_response(data)

    def form_invalid(self, form):
        data = {"form": form}
        return self.render_to_response(data)

    def post(self, request, *args, **kwargs):
        form = PlanForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class AjaxSubscribe(EldarionAjaxResponseMixin, CustomerMixin, View):

    form_class = PlanForm
    template_fragment = "payments/_subscribe_form.html"

    def redirect(self):
        return self.response_class(
            data=self.render_location(self.get_success_url()),
            encoder=self.encoder_class,
            safe=self.safe
        )

    def get_success_url(self):
        return reverse("payments_history")

    def set_customer(self):
        try:
            self.customer
        except ObjectDoesNotExist:
            self._customer = Customer.create(self.request.user)

    def update_card(self, token):
        if token:
            self.customer.update_card(token)

    def form_valid(self, form):
        data = {"plans": settings.PINAX_STRIPE_PLANS}
        self.set_customer()
        try:
            if self.request.POST.get("stripe_token"):
                self.update_card(self.request.POST.get("stripe_token"))
            self.customer.subscribe(plan=form.cleaned_data["plan"])
            return self.redirect()
        except stripe.StripeError as e:
            data["form"] = form
            data["error"] = smart_str(e) or "Unknown error"
        return self.render_to_response(data)

    def form_invalid(self, form):
        data = {
            "error": form.errors,
            "form": form
        }
        return self.render_to_response(data)

    def post(self, request, *args, **kwargs):
        form = PlanForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class AjaxCancelSubscription(EldarionAjaxResponseMixin, CustomerMixin, View):

    template_fragment = "payments/_cancel_form.html"

    def post(self, request, *args, **kwargs):
        try:
            self.customer.cancel()
            data = {}
        except stripe.StripeError as e:
            data = {"error": smart_str(e)}
        return self.render_to_response(data)


class Webhook(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(Webhook, self).dispatch(*args, **kwargs)

    def extract_json(self):
        data = json.loads(smart_str(self.request.body))
        return data

    def dupe_exists(self, stripe_id):
        return Event.objects.filter(stripe_id=stripe_id).exists()

    def log_exception(self, data):
        EventProcessingException.objects.create(
            data=data,
            message="Duplicate event record",
            traceback=""
        )

    def add_event(self, stripe_id, kind, livemode, message):
        event = Event.objects.create(
            stripe_id=stripe_id,
            kind=kind,
            livemode=livemode,
            webhook_message=message
        )
        event.validate()
        event.process()

    def post(self, request, *args, **kwargs):
        data = self.extract_json()
        if self.dupe_exists(data["id"]):
            self.log_exception(data)
        else:
            self.add_event(
                stripe_id=data["id"],
                kind=data["type"],
                livemode=data["livemode"],
                message=data
            )
        return HttpResponse()
