# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_stripe', '0008_auto_20170509_1736'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(null=True)),
                ('end', models.DateTimeField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='coupon',
            name='duration',
            field=models.CharField(choices=[('forever', 'forever'), ('once', 'once'), ('repeating', 'repeating')], default='once', max_length=10),
        ),
        migrations.AddField(
            model_name='discount',
            name='coupon',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pinax_stripe.Coupon'),
        ),
        migrations.AddField(
            model_name='discount',
            name='customer',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='pinax_stripe.Customer'),
        ),
        migrations.AddField(
            model_name='discount',
            name='subscription',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='pinax_stripe.Subscription'),
        ),
    ]
