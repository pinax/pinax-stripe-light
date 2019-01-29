# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import connection, migrations, models


def migrate_customers(apps, schema_editor):
    cursor = connection.cursor()
    if "payments_customer" in connection.introspection.table_names():
        cursor.execute("SELECT user_id, stripe_id, date_purged FROM payments_customer")
        Customer = apps.get_model("pinax_stripe", "Customer")
        for row in cursor.fetchall():
            Customer.objects.create(
                user_id=row[0],
                stripe_id=row[1],
                date_purged=row[2]
            )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pinax_stripe', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_customers)
    ]
