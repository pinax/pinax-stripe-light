# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_stripe', '0003_make_cvc_check_blankable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='country',
            field=models.CharField(blank=True, max_length=2),
        ),
    ]
