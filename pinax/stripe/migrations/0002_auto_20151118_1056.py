# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_stripe', '0001_initial'),
    ]

    operations = [
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
            name='CurrentSubscriptionProxy',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('pinax_stripe.currentsubscription',),
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
                'ordering': ['-date'],
                'proxy': True,
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
    ]
