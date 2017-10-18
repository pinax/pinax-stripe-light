# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-18 10:24
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pinax_stripe', '0013_revert_0011'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='useraccount',
            unique_together=set([('user', 'account')]),
        ),
    ]