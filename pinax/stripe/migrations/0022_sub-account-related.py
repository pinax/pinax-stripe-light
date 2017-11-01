# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-26 12:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_stripe', '0021_account-authorized'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='stripe_account',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='pinax_stripe.Account'),
        ),
    ]