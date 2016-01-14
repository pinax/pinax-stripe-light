import json

from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_str
from django.views.generic import TemplateView, DetailView, View, FormView, ListView
from django.views.generic.edit import FormMixin
from django.views.decorators.csrf import csrf_exempt

import stripe

from .actions import events, exceptions, customers, subscriptions, sources
from .forms import PlanForm, PaymentMethodForm
from .mixins import LoginRequiredMixin, CustomerMixin, PaymentsContextMixin
from .models import Invoice, Card, Subscription


class InvoiceListView(LoginRequiredMixin, CustomerMixin, ListView):
    model = Invoice
    context_object_name = "invoice_list"
    template_name = "pinax/stripe/invoice_list.html"

    def get_queryset(self):
        return super(InvoiceListView, self).get_queryset().order_by("date")


class PaymentMethodListView(LoginRequiredMixin, CustomerMixin, ListView):
    model = Card
    context_object_name = "payment_method_list"
    template_name = "pinax/stripe/paymentmethod_list.html"

    def get_queryset(self):
        return super(PaymentMethodListView, self).get_queryset().order_by("created_at")


class PaymentMethodCreateView(LoginRequiredMixin, CustomerMixin, PaymentsContextMixin, TemplateView):
    model = Card
    template_name = "pinax/stripe/paymentmethod_create.html"

    def create_card(self, stripe_token):
        sources.create_card(self.customer, token=stripe_token)

    def post(self, request, *args, **kwargs):
        try:
            self.create_card(request.POST.get("stripeToken"))
            return redirect("pinax_stripe_payment_method_list")
        except stripe.CardError as e:
            return self.render_to_response(self.get_context_data(errors=smart_str(e)))


class PaymentMethodDeleteView(LoginRequiredMixin, CustomerMixin, DetailView):
    model = Card
    template_name = "pinax/stripe/paymentmethod_delete.html"

    def delete_card(self, stripe_id):
        sources.delete_card(self.customer, stripe_id)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.delete_card(self.object.stripe_id)
            return redirect("pinax_stripe_payment_method_list")
        except stripe.CardError as e:
            return self.render_to_response(self.get_context_data(errors=smart_str(e)))


class PaymentMethodUpdateView(LoginRequiredMixin, CustomerMixin, PaymentsContextMixin, FormMixin, DetailView):
    model = Card
    form_class = PaymentMethodForm
    template_name = "pinax/stripe/paymentmethod_update.html"

    def update_card(self, exp_month, exp_year):
        sources.update_card(self.customer, self.object.stripe_id, exp_month=exp_month, exp_year=exp_year)

    def form_valid(self, form):
        try:
            self.update_card(form.cleaned_data["expMonth"], form.cleaned_data["expYear"])
            return redirect("pinax_stripe_payment_method_list")
        except stripe.CardError as e:
            return self.render_to_response(self.get_context_data(errors=smart_str(e)))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(form_class=self.form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class SubscriptionListView(LoginRequiredMixin, CustomerMixin, ListView):
    model = Subscription
    context_object_name = "subscription_list"
    template_name = "pinax/stripe/subscription_list.html"

    def get_queryset(self):
        return super(SubscriptionListView, self).get_queryset().order_by("created_at")


class SubscriptionCreateView(LoginRequiredMixin, PaymentsContextMixin, CustomerMixin, FormView):
    template_name = "pinax/stripe/subscription_create.html"
    form_class = PlanForm

    def set_customer(self):
        if self.customer is None:
            self._customer = customers.create(self.request.user)

    def subscribe(self, customer, plan, token):
        subscriptions.create(customer, plan, token=token)

    def form_valid(self, form):
        self.set_customer()
        try:
            self.subscribe(self.customer, plan=form.cleaned_data["plan"], token=self.request.POST.get("stripeToken"))
            return redirect("pinax_stripe_subscription_list")
        except stripe.StripeError as e:
            return self.render_to_response(self.get_context_data(form=form, errors=smart_str(e)))


class SubscriptionDeleteView(LoginRequiredMixin, CustomerMixin, DetailView):
    model = Subscription
    template_name = "pinax/stripe/subscription_delete.html"

    def cancel(self):
        subscriptions.cancel(self.object)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.cancel()
            return redirect("pinax_stripe_subscription_list")
        except stripe.StripeError as e:
            return self.render_to_response(self.get_context_data(errors=smart_str(e)))


class SubscriptionUpdateView(LoginRequiredMixin, CustomerMixin, FormMixin, DetailView):
    model = Subscription
    form_class = PlanForm
    template_name = "pinax/stripe/subscription_update.html"

    @property
    def current_plan(self):
        if not hasattr(self, "_current_plan"):
            self._current_plan = self.object.plan
        return self._current_plan

    def get_context_data(self, **kwargs):
        context = super(SubscriptionUpdateView, self).get_context_data(**kwargs)
        context.update({
            "form": self.get_form(form_class=self.form_class)
        })
        return context

    def update_subscription(self, plan_id):
        subscriptions.update(self.object, plan_id)

    def get_initial(self):
        initial = super(SubscriptionUpdateView, self).get_initial()
        initial.update({
            "plan": self.current_plan
        })
        return initial

    def form_valid(self, form):
        try:
            self.update_subscription(form.cleaned_data["plan"])
            return redirect("pinax_stripe_subscription_list")
        except stripe.StripeError as e:
            return self.render_to_response(self.get_context_data(form=form, errors=smart_str(e)))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(form_class=self.form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


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
            exceptions.log_exception(data, "Duplicate event record")
        else:
            events.add_event(
                stripe_id=data["id"],
                kind=data["type"],
                livemode=data["livemode"],
                message=data
            )
        return HttpResponse()
