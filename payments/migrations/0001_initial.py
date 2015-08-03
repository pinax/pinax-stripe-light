# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('card_last_4', models.CharField(max_length=4, blank=True)),
                ('card_kind', models.CharField(max_length=50, blank=True)),
                ('currency', models.CharField(default=b'usd', max_length=10)),
                ('amount', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('amount_refunded', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('description', models.TextField(blank=True)),
                ('paid', models.NullBooleanField()),
                ('disputed', models.NullBooleanField()),
                ('refunded', models.NullBooleanField()),
                ('captured', models.NullBooleanField()),
                ('fee', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('receipt_sent', models.BooleanField(default=False)),
                ('charge_created', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CurrentSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('plan', models.CharField(max_length=100)),
                ('quantity', models.IntegerField()),
                ('start', models.DateTimeField()),
                ('status', models.CharField(max_length=25)),
                ('cancel_at_period_end', models.BooleanField(default=False)),
                ('canceled_at', models.DateTimeField(null=True, blank=True)),
                ('current_period_end', models.DateTimeField(null=True, blank=True)),
                ('current_period_start', models.DateTimeField(null=True, blank=True)),
                ('ended_at', models.DateTimeField(null=True, blank=True)),
                ('trial_end', models.DateTimeField(null=True, blank=True)),
                ('trial_start', models.DateTimeField(null=True, blank=True)),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('currency', models.CharField(default=b'usd', max_length=10)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('card_fingerprint', models.CharField(max_length=200, blank=True)),
                ('card_last_4', models.CharField(max_length=4, blank=True)),
                ('card_kind', models.CharField(max_length=50, blank=True)),
                ('date_purged', models.DateTimeField(null=True, editable=False)),
                ('user', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('kind', models.CharField(max_length=250)),
                ('livemode', models.BooleanField(default=False)),
                ('webhook_message', jsonfield.fields.JSONField()),
                ('validated_message', jsonfield.fields.JSONField(null=True)),
                ('valid', models.NullBooleanField()),
                ('processed', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(to='payments.Customer', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EventProcessingException',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.TextField()),
                ('message', models.CharField(max_length=500)),
                ('traceback', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('event', models.ForeignKey(to='payments.Event', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(max_length=255)),
                ('attempted', models.NullBooleanField()),
                ('attempts', models.PositiveIntegerField(null=True)),
                ('closed', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('period_end', models.DateTimeField()),
                ('period_start', models.DateTimeField()),
                ('subtotal', models.DecimalField(max_digits=9, decimal_places=2)),
                ('total', models.DecimalField(max_digits=9, decimal_places=2)),
                ('currency', models.CharField(default=b'usd', max_length=10)),
                ('date', models.DateTimeField()),
                ('charge', models.CharField(max_length=50, blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('customer', models.ForeignKey(related_name='invoices', to='payments.Customer')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('currency', models.CharField(default=b'usd', max_length=10)),
                ('period_start', models.DateTimeField()),
                ('period_end', models.DateTimeField()),
                ('proration', models.BooleanField(default=False)),
                ('line_type', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=200, blank=True)),
                ('plan', models.CharField(max_length=100, blank=True)),
                ('quantity', models.IntegerField(null=True)),
                ('invoice', models.ForeignKey(related_name='items', to='payments.Invoice')),
            ],
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_id', models.CharField(unique=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('currency', models.CharField(default=b'usd', max_length=25)),
                ('status', models.CharField(max_length=25)),
                ('date', models.DateTimeField()),
                ('description', models.TextField(null=True, blank=True)),
                ('adjustment_count', models.IntegerField(null=True)),
                ('adjustment_fees', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('adjustment_gross', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('charge_count', models.IntegerField(null=True)),
                ('charge_fees', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('charge_gross', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('collected_fee_count', models.IntegerField(null=True)),
                ('collected_fee_gross', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('net', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('refund_count', models.IntegerField(null=True)),
                ('refund_fees', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('refund_gross', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('validation_count', models.IntegerField(null=True)),
                ('validation_fees', models.DecimalField(null=True, max_digits=9, decimal_places=2)),
                ('event', models.ForeignKey(related_name='transfers', to='payments.Event')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TransferChargeFee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('currency', models.CharField(default=b'usd', max_length=10)),
                ('application', models.TextField(null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('kind', models.CharField(max_length=150)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('transfer', models.ForeignKey(related_name='charge_fee_details', to='payments.Transfer')),
            ],
        ),
        migrations.AddField(
            model_name='currentsubscription',
            name='customer',
            field=models.OneToOneField(related_name='current_subscription', null=True, to='payments.Customer'),
        ),
        migrations.AddField(
            model_name='charge',
            name='customer',
            field=models.ForeignKey(related_name='charges', to='payments.Customer'),
        ),
        migrations.AddField(
            model_name='charge',
            name='invoice',
            field=models.ForeignKey(related_name='charges', to='payments.Invoice', null=True),
        ),
    ]
