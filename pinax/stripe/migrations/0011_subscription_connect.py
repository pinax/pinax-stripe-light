from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_stripe', '0010_connect'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='stripe_account',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
