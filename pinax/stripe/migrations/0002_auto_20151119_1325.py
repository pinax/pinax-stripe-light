# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from decimal import Decimal
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_stripe', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BitcoinReceiver',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('active', models.BooleanField(default=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('amount_received', models.DecimalField(decimal_places=2, max_digits=9, default=Decimal('0'))),
                ('bitcoin_amount', models.PositiveIntegerField()),
                ('bitcoin_amount_received', models.PositiveIntegerField(default=0)),
                ('bitcoin_uri', models.TextField(blank=True)),
                ('currency', models.CharField(max_length=10, default=b'usd')),
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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
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
            name='Subscription',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('application_fee_percent', models.DecimalField(decimal_places=2, max_digits=3, null=True, default=None)),
                ('cancel_at_period_end', models.BooleanField(default=False)),
                ('canceled_at', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('plan', models.CharField(max_length=100)),
                ('quantity', models.IntegerField()),
                ('start', models.DateTimeField()),
                ('status', models.CharField(max_length=25)),
                ('trial_end', models.DateTimeField(blank=True, null=True)),
                ('trial_start', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='currentsubscription',
            name='customer',
        ),
        migrations.CreateModel(
            name='ChargeProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.charge',),
        ),
        migrations.CreateModel(
            name='CustomerProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.customer',),
        ),
        migrations.CreateModel(
            name='EventProcessingExceptionProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.eventprocessingexception',),
        ),
        migrations.CreateModel(
            name='EventProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.event',),
        ),
        migrations.CreateModel(
            name='InvoiceProxy',
            fields=[
            ],
            options={
                'proxy': True,
                'ordering': ['-date'],
            },
            bases=('pinax_stripe.invoice',),
        ),
        migrations.CreateModel(
            name='TransferProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.transfer',),
        ),
        migrations.AlterModelOptions(
            name='invoice',
            options={},
        ),
        migrations.RenameField(
            model_name='invoice',
            old_name='attempts',
            new_name='attempt_count',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='card_fingerprint',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='card_kind',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='card_last_4',
        ),
        migrations.AddField(
            model_name='customer',
            name='account_balance',
            field=models.DecimalField(decimal_places=2, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='currency',
            field=models.CharField(blank=True, max_length=10, default=b'usd'),
        ),
        migrations.AddField(
            model_name='customer',
            name='default_source',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='delinquent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event',
            name='api_version',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='event',
            name='pending_webhooks',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='event',
            name='request',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='invoice',
            name='amount_due',
            field=models.DecimalField(decimal_places=2, max_digits=9, default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoice',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='receipt_number',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='statement_descriptor',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='webhooks_delivered_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='kind',
            field=models.CharField(blank=True, max_length=25),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='charge',
            field=models.ForeignKey(null=True, related_name='invoices', to='pinax_stripe.Charge'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='stripe_id',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='stripe_id',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.DeleteModel(
            name='CurrentSubscription',
        ),
        migrations.AddField(
            model_name='subscription',
            name='customer',
            field=models.ForeignKey(to='pinax_stripe.Customer'),
        ),
        migrations.AddField(
            model_name='card',
            name='customer',
            field=models.ForeignKey(to='pinax_stripe.Customer'),
        ),
        migrations.AddField(
            model_name='bitcoinreceiver',
            name='customer',
            field=models.ForeignKey(to='pinax_stripe.Customer'),
        ),
        migrations.CreateModel(
            name='BitcoinRecieverProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.bitcoinreceiver',),
        ),
        migrations.CreateModel(
            name='CardProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.card',),
        ),
        migrations.CreateModel(
            name='SubscriptionProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.subscription',),
        ),
        migrations.AddField(
            model_name='invoice',
            name='subscription',
            field=models.ForeignKey(null=True, to='pinax_stripe.Subscription'),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='subscription',
            field=models.ForeignKey(null=True, to='pinax_stripe.Subscription'),
        ),
    ]
