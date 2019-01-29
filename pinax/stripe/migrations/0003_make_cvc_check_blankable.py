# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_stripe', '0002_auto_20151205_1451'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='cvc_check',
            field=models.CharField(blank=True, max_length=15),
        ),
    ]
