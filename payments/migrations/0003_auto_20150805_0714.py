# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_customer_questions_asked'),
        ('authentication', '0010_auto_20150805_0612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='user',
            field=models.OneToOneField("authentication.EmailUser", null=True),
            preserve_default=True,
        ),
    ]
