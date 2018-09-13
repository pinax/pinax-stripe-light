.PHONY: makemigrations mergemigrations

makemigrations mergemigrations: PINAX_STRIPE_DATABASE_ENGINE=django.db.backends.sqlite3

makemigrations:
	django-admin makemigrations pinax_stripe

mergemigrations:
	django-admin makemigrations --merge pinax_stripe
