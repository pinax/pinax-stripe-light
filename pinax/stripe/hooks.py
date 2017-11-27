from django.core.mail import EmailMessage
from django.template.loader import render_to_string


class DefaultHookSet(object):

    def adjust_subscription_quantity(self, customer, plan, quantity):
        """
        Given a customer, plan, and quantity, when calling Customer.subscribe
        you have the opportunity to override the quantity that was specified.

        Previously this was handled in the setting `PAYMENTS_PLAN_QUANTITY_CALLBACK`
        and was only passed a customer object.
        """
        if quantity is None:
            quantity = 1
        return quantity

    def trial_period(self, user, plan):
        """
        Given a user and plan, return an end date for a trial period, or None
        for no trial period.

        Was previously in the setting `TRIAL_PERIOD_FOR_USER_CALLBACK`
        """
        return None

    def send_receipt(self, charge, email=None):
        from django.conf import settings
        if not charge.receipt_sent:
            # Import here to not add a hard dependency on the Sites framework
            from django.contrib.sites.models import Site

            site = Site.objects.get_current()
            protocol = getattr(settings, "DEFAULT_HTTP_PROTOCOL", "http")
            ctx = {
                "charge": charge,
                "site": site,
                "protocol": protocol,
            }
            subject = render_to_string("pinax/stripe/email/subject.txt", ctx)
            subject = subject.strip()
            message = render_to_string("pinax/stripe/email/body.txt", ctx)

            if not email and charge.customer:
                email = charge.customer.user.email

            num_sent = EmailMessage(
                subject,
                message,
                to=[email],
                from_email=settings.PINAX_STRIPE_INVOICE_FROM_EMAIL
            ).send()
            charge.receipt_sent = num_sent and num_sent > 0
            charge.save()


class HookProxy(object):

    def __getattr__(self, attr):
        from .conf import settings  # if put globally there is a race condition
        return getattr(settings.PINAX_STRIPE_HOOKSET, attr)


hookset = HookProxy()
