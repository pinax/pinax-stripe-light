# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_stripe', '0005_auto_20161006_1445'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='customer',
            field=models.ForeignKey(related_name='subscriptions', to='pinax_stripe.Customer'),
        ),
    ]
