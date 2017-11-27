# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BitcoinReceiver',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('active', models.BooleanField(default=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('amount_received', models.DecimalField(decimal_places=2, max_digits=9, default=Decimal('0'))),
                ('bitcoin_amount', models.PositiveIntegerField()),
                ('bitcoin_amount_received', models.PositiveIntegerField(default=0)),
                ('bitcoin_uri', models.TextField(blank=True)),
                ('currency', models.CharField(max_length=10, default='usd')),
                ('description', models.TextField(blank=True)),
                ('email', models.TextField(blank=True)),
                ('filled', models.BooleanField(default=False)),
                ('inbound_address', models.TextField(blank=True)),
                ('payment', models.TextField(blank=True)),
                ('refund_address', models.TextField(blank=True)),
                ('uncaptured_funds', models.BooleanField(default=False)),
                ('used_for_payment', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.TextField(blank=True)),
                ('address_line_1', models.TextField(blank=True)),
                ('address_line_1_check', models.CharField(max_length=15)),
                ('address_line_2', models.TextField(blank=True)),
                ('address_city', models.TextField(blank=True)),
                ('address_state', models.TextField(blank=True)),
                ('address_country', models.TextField(blank=True)),
                ('address_zip', models.TextField(blank=True)),
                ('address_zip_check', models.CharField(max_length=15)),
                ('brand', models.TextField(blank=True)),
                ('country', models.CharField(max_length=2)),
                ('cvc_check', models.CharField(max_length=15)),
                ('dynamic_last4', models.CharField(blank=True, max_length=4)),
                ('tokenization_method', models.CharField(blank=True, max_length=15)),
                ('exp_month', models.IntegerField()),
                ('exp_year', models.IntegerField()),
                ('funding', models.CharField(max_length=15)),
                ('last4', models.CharField(blank=True, max_length=4)),
                ('fingerprint', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('source', models.CharField(max_length=100)),
                ('currency', models.CharField(max_length=10, default='usd')),
                ('amount', models.DecimalField(null=True, decimal_places=2, max_digits=9)),
                ('amount_refunded', models.DecimalField(null=True, decimal_places=2, max_digits=9)),
                ('description', models.TextField(blank=True)),
                ('paid', models.NullBooleanField()),
                ('disputed', models.NullBooleanField()),
                ('refunded', models.NullBooleanField()),
                ('captured', models.NullBooleanField()),
                ('receipt_sent', models.BooleanField(default=False)),
                ('charge_created', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('account_balance', models.DecimalField(null=True, decimal_places=2, max_digits=9)),
                ('currency', models.CharField(blank=True, max_length=10, default='usd')),
                ('delinquent', models.BooleanField(default=False)),
                ('default_source', models.TextField(blank=True)),
                ('date_purged', models.DateTimeField(null=True, editable=False)),
                ('user', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('kind', models.CharField(max_length=250)),
                ('livemode', models.BooleanField(default=False)),
                ('webhook_message', jsonfield.fields.JSONField()),
                ('validated_message', jsonfield.fields.JSONField(null=True)),
                ('valid', models.NullBooleanField()),
                ('processed', models.BooleanField(default=False)),
                ('request', models.CharField(blank=True, max_length=100)),
                ('pending_webhooks', models.PositiveIntegerField(default=0)),
                ('api_version', models.CharField(blank=True, max_length=100)),
                ('customer', models.ForeignKey(null=True, to='pinax_stripe.Customer', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EventProcessingException',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('data', models.TextField()),
                ('message', models.CharField(max_length=500)),
                ('traceback', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('event', models.ForeignKey(null=True, to='pinax_stripe.Event', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount_due', models.DecimalField(decimal_places=2, max_digits=9)),
                ('attempted', models.NullBooleanField()),
                ('attempt_count', models.PositiveIntegerField(null=True)),
                ('statement_descriptor', models.TextField(blank=True)),
                ('currency', models.CharField(max_length=10, default='usd')),
                ('closed', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True)),
                ('paid', models.BooleanField(default=False)),
                ('receipt_number', models.TextField(blank=True)),
                ('period_end', models.DateTimeField()),
                ('period_start', models.DateTimeField()),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=9)),
                ('total', models.DecimalField(decimal_places=2, max_digits=9)),
                ('date', models.DateTimeField()),
                ('webhooks_delivered_at', models.DateTimeField(null=True)),
                ('charge', models.ForeignKey(null=True, related_name='invoices', to='pinax_stripe.Charge', on_delete=models.CASCADE)),
                ('customer', models.ForeignKey(related_name='invoices', to='pinax_stripe.Customer', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('currency', models.CharField(max_length=10, default='usd')),
                ('kind', models.CharField(blank=True, max_length=25)),
                ('period_start', models.DateTimeField()),
                ('period_end', models.DateTimeField()),
                ('proration', models.BooleanField(default=False)),
                ('line_type', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('quantity', models.IntegerField(null=True)),
                ('invoice', models.ForeignKey(related_name='items', to='pinax_stripe.Invoice', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('currency', models.CharField(max_length=15)),
                ('interval', models.CharField(max_length=15)),
                ('interval_count', models.IntegerField()),
                ('name', models.CharField(max_length=150)),
                ('statement_descriptor', models.TextField(blank=True)),
                ('trial_period_days', models.IntegerField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('application_fee_percent', models.DecimalField(null=True, decimal_places=2, max_digits=3, default=None)),
                ('cancel_at_period_end', models.BooleanField(default=False)),
                ('canceled_at', models.DateTimeField(null=True, blank=True)),
                ('current_period_end', models.DateTimeField(null=True, blank=True)),
                ('current_period_start', models.DateTimeField(null=True, blank=True)),
                ('ended_at', models.DateTimeField(null=True, blank=True)),
                ('quantity', models.IntegerField()),
                ('start', models.DateTimeField()),
                ('status', models.CharField(max_length=25)),
                ('trial_end', models.DateTimeField(null=True, blank=True)),
                ('trial_start', models.DateTimeField(null=True, blank=True)),
                ('customer', models.ForeignKey(to='pinax_stripe.Customer', on_delete=models.CASCADE)),
                ('plan', models.ForeignKey(to='pinax_stripe.Plan', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('stripe_id', models.CharField(unique=True, max_length=191)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('currency', models.CharField(max_length=25, default='usd')),
                ('status', models.CharField(max_length=25)),
                ('date', models.DateTimeField()),
                ('description', models.TextField(null=True, blank=True)),
                ('event', models.ForeignKey(related_name='transfers', to='pinax_stripe.Event', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TransferChargeFee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('currency', models.CharField(max_length=10, default='usd')),
                ('application', models.TextField(null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('kind', models.CharField(max_length=150)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('transfer', models.ForeignKey(related_name='charge_fee_details', to='pinax_stripe.Transfer', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='plan',
            field=models.ForeignKey(null=True, to='pinax_stripe.Plan', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='subscription',
            field=models.ForeignKey(null=True, to='pinax_stripe.Subscription', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='invoice',
            name='subscription',
            field=models.ForeignKey(null=True, to='pinax_stripe.Subscription', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='charge',
            name='customer',
            field=models.ForeignKey(related_name='charges', to='pinax_stripe.Customer', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='charge',
            name='invoice',
            field=models.ForeignKey(null=True, related_name='charges', to='pinax_stripe.Invoice', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='card',
            name='customer',
            field=models.ForeignKey(to='pinax_stripe.Customer', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='bitcoinreceiver',
            name='customer',
            field=models.ForeignKey(to='pinax_stripe.Customer', on_delete=models.CASCADE),
        ),
    ]
