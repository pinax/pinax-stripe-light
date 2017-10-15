from django.template import Context, Template
from django.test import TestCase, override_settings


class TemplateTagTests(TestCase):

    @override_settings(PINAX_STRIPE_PUBLIC_KEY="this-is-the-stripe-public-key")
    def test_stripe_public_key(self):
        self.maxDiff = None
        template = Template("""{% load stripe %}
            <script>
                Stripe.setPublishableKey({% stripe_public_key %});
            </script>
            """)

        self.assertEqual(
            template.render(Context()),
            """
            <script>
                Stripe.setPublishableKey('this-is-the-stripe-public-key');
            </script>
            """
        )

    def test_no_stripe_public_key(self):
        self.maxDiff = None
        template = Template("""{% load stripe %}
            <script>
                Stripe.setPublishableKey({% stripe_public_key %});
            </script>
            """)

        self.assertEqual(
            template.render(Context()),
            """
            <script>
                Stripe.setPublishableKey(*** PINAX_STRIPE_PUBLIC_KEY NOT SET ***);
            </script>
            """
        )
