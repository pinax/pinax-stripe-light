import os

USE_TZ = True
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("PINAX_STRIPE_DATABASE_ENGINE", "django.db.backends.sqlite3"),
        "HOST": os.environ.get("PINAX_STRIPE_DATABASE_HOST", "127.0.0.1"),
        "NAME": os.environ.get("PINAX_STRIPE_DATABASE_NAME", "pinax_stripe"),
        "USER": os.environ.get("PINAX_STRIPE_DATABASE_USER", ""),
    }
}
ROOT_URLCONF = "pinax.stripe.tests.urls"
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "pinax.stripe",
]
SITE_ID = 1
PINAX_STRIPE_PUBLIC_KEY = ""
PINAX_STRIPE_SECRET_KEY = "sk_test_01234567890123456789abcd"
PINAX_STRIPE_ENDPOINT_SECRET = "foo"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "OPTIONS": {
        "context_processors": [
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "django.template.context_processors.request",
        ]
    }
}]
SECRET_KEY = "pinax-stripe-secret-key"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
