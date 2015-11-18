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

from .actions import events, customers
from .conf import settings
from .forms import PlanForm, PLAN_CHOICES


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
    template_name = "pinax/stripe/subscribe.html"

    def get_context_data(self, **kwargs):
        context = super(SubscribeView, self).get_context_data(**kwargs)
        context.update({
            "form": PlanForm
        })
        return context


class ChangeCardView(PaymentsContextMixin, TemplateView):
    template_name = "pinax/stripe/change_card.html"


class CancelView(PaymentsContextMixin, TemplateView):
    template_name = "pinax/stripe/cancel.html"


class ChangePlanView(SubscribeView):
    template_name = "pinax/stripe/change_plan.html"


class HistoryView(PaymentsContextMixin, TemplateView):
    template_name = "pinax/stripe/history.html"


class CustomerMixin(object):

    @property
    def customer(self):
        if not hasattr(self, "_customer"):
            self._customer = customers.get_customer_for_user(self.request.user)
        return self._customer


class AjaxChangeCard(EldarionAjaxResponseMixin, CustomerMixin, View):

    template_fragment = "pinax/stripe/_change_card_form.html"

    def send_invoice(self):
        if self.customer.card_fingerprint == "":
            self.customer.send_invoice()

    def update_card(self, stripe_token):
        self.customer.update_card(stripe_token)

    def retry_unpaid_invoices(self):
        customers.retry_unpaid_invoices(self.customer)

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
    template_fragment = "pinax/stripe/_change_plan_form.html"

    @property
    def current_plan(self):
        if not hasattr(self, "_current_plan"):
            sub = self.customer.current_subscription()
            if sub:
                self._current_plan = sub.plan
        return self._current_plan

    def subscribe(self, plan):
        try:
            customers.subscribe(self.customer, plan)
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
    template_fragment = "pinax/stripe/_subscribe_form.html"

    def redirect(self):
        return self.response_class(
            data=self.render_location(self.get_success_url()),
            encoder=self.encoder_class,
            safe=self.safe
        )

    def get_success_url(self):
        return reverse("pinax_stripe_history")

    def set_customer(self):
        try:
            self.customer
        except ObjectDoesNotExist:
            self._customer = customers.create_customer(self.request.user)

    def update_card(self, token):
        if token:
            self.customer.update_card(token)

    def form_valid(self, form):
        data = {"plans": settings.PINAX_STRIPE_PLANS}
        self.set_customer()
        try:
            if self.request.POST.get("stripe_token"):
                self.update_card(self.request.POST.get("stripe_token"))
            customers.subscribe(self.customer, plan=form.cleaned_data["plan"])
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

    template_fragment = "pinax/stripe/_cancel_form.html"

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

    def post(self, request, *args, **kwargs):
        data = self.extract_json()
        if events.dupe_event_exists(data["id"]):
            events.log_exception(data, "Duplicate event record")
        else:
            events.add_event(
                stripe_id=data["id"],
                kind=data["type"],
                livemode=data["livemode"],
                message=data
            )
        return HttpResponse()
