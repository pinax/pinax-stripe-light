# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EventProcessingException'
        db.create_table(u'payments_eventprocessingexception', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['payments.Event'], null=True)),
            ('data', self.gf('django.db.models.fields.TextField')()),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('traceback', self.gf('django.db.models.fields.TextField')()),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'payments', ['EventProcessingException'])

        # Adding model 'Event'
        db.create_table(u'payments_event', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stripe_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('kind', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('livemode', self.gf('django.db.models.fields.BooleanField')()),
            ('customer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['payments.Customer'], null=True)),
            ('webhook_message', self.gf('jsonfield.fields.JSONField')(default={})),
            ('validated_message', self.gf('jsonfield.fields.JSONField')(null=True)),
            ('valid', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('processed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'payments', ['Event'])

        # Adding model 'Transfer'
        db.create_table(u'payments_transfer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stripe_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='transfers', to=orm['payments.Event'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=25)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('adjustment_count', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('adjustment_fees', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('adjustment_gross', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('charge_count', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('charge_fees', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('charge_gross', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('collected_fee_count', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('collected_fee_gross', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('net', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('refund_count', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('refund_fees', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('refund_gross', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('validation_count', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('validation_fees', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
        ))
        db.send_create_signal(u'payments', ['Transfer'])

        # Adding model 'TransferChargeFee'
        db.create_table(u'payments_transferchargefee', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('transfer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='charge_fee_details', to=orm['payments.Transfer'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=10)),
            ('application', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('kind', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'payments', ['TransferChargeFee'])

        # Adding model 'Customer'
        db.create_table(u'payments_customer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stripe_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, null=True)),
            ('card_fingerprint', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('card_last_4', self.gf('django.db.models.fields.CharField')(max_length=4, blank=True)),
            ('card_kind', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('date_purged', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'payments', ['Customer'])

        # Adding model 'CurrentSubscription'
        db.create_table(u'payments_currentsubscription', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('customer', self.gf('django.db.models.fields.related.OneToOneField')(related_name='current_subscription', unique=True, null=True, to=orm['payments.Customer'])),
            ('plan', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')()),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('cancel_at_period_end', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('canceled_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('current_period_end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('current_period_start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ended_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('trial_end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('trial_start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=10)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'payments', ['CurrentSubscription'])

        # Adding model 'Invoice'
        db.create_table(u'payments_invoice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stripe_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('customer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invoices', to=orm['payments.Customer'])),
            ('attempted', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('attempts', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('paid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('period_end', self.gf('django.db.models.fields.DateTimeField')()),
            ('period_start', self.gf('django.db.models.fields.DateTimeField')()),
            ('subtotal', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('total', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=10)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('charge', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'payments', ['Invoice'])

        # Adding model 'InvoiceItem'
        db.create_table(u'payments_invoiceitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stripe_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('invoice', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['payments.Invoice'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=10)),
            ('period_start', self.gf('django.db.models.fields.DateTimeField')()),
            ('period_end', self.gf('django.db.models.fields.DateTimeField')()),
            ('proration', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('line_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('plan', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'payments', ['InvoiceItem'])

        # Adding model 'Charge'
        db.create_table(u'payments_charge', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stripe_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('customer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='charges', to=orm['payments.Customer'])),
            ('invoice', self.gf('django.db.models.fields.related.ForeignKey')(related_name='charges', null=True, to=orm['payments.Invoice'])),
            ('card_last_4', self.gf('django.db.models.fields.CharField')(max_length=4, blank=True)),
            ('card_kind', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=10)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('amount_refunded', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('paid', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('disputed', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('refunded', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('fee', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=2)),
            ('receipt_sent', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('charge_created', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'payments', ['Charge'])


    def backwards(self, orm):
        # Deleting model 'EventProcessingException'
        db.delete_table(u'payments_eventprocessingexception')

        # Deleting model 'Event'
        db.delete_table(u'payments_event')

        # Deleting model 'Transfer'
        db.delete_table(u'payments_transfer')

        # Deleting model 'TransferChargeFee'
        db.delete_table(u'payments_transferchargefee')

        # Deleting model 'Customer'
        db.delete_table(u'payments_customer')

        # Deleting model 'CurrentSubscription'
        db.delete_table(u'payments_currentsubscription')

        # Deleting model 'Invoice'
        db.delete_table(u'payments_invoice')

        # Deleting model 'InvoiceItem'
        db.delete_table(u'payments_invoiceitem')

        # Deleting model 'Charge'
        db.delete_table(u'payments_charge')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'payments.charge': {
            'Meta': {'object_name': 'Charge'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'amount_refunded': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'card_kind': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'card_last_4': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'charge_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '10'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charges'", 'to': u"orm['payments.Customer']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'disputed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'fee': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charges'", 'null': 'True', 'to': u"orm['payments.Invoice']"}),
            'paid': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'receipt_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'refunded': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'payments.currentsubscription': {
            'Meta': {'object_name': 'CurrentSubscription'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'cancel_at_period_end': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'canceled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '10'}),
            'current_period_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'current_period_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'customer': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'current_subscription'", 'unique': 'True', 'null': 'True', 'to': u"orm['payments.Customer']"}),
            'ended_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plan': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'trial_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'trial_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'payments.customer': {
            'Meta': {'object_name': 'Customer'},
            'card_fingerprint': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'card_kind': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'card_last_4': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_purged': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True', 'null': 'True'})
        },
        u'payments.event': {
            'Meta': {'object_name': 'Event'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['payments.Customer']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'livemode': ('django.db.models.fields.BooleanField', [], {}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'valid': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'validated_message': ('jsonfield.fields.JSONField', [], {'null': 'True'}),
            'webhook_message': ('jsonfield.fields.JSONField', [], {'default': '{}'})
        },
        u'payments.eventprocessingexception': {
            'Meta': {'object_name': 'EventProcessingException'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['payments.Event']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'traceback': ('django.db.models.fields.TextField', [], {})
        },
        u'payments.invoice': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Invoice'},
            'attempted': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'attempts': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'charge': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '10'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invoices'", 'to': u"orm['payments.Customer']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'period_end': ('django.db.models.fields.DateTimeField', [], {}),
            'period_start': ('django.db.models.fields.DateTimeField', [], {}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subtotal': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'total': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'})
        },
        u'payments.invoiceitem': {
            'Meta': {'object_name': 'InvoiceItem'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '10'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['payments.Invoice']"}),
            'line_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'period_end': ('django.db.models.fields.DateTimeField', [], {}),
            'period_start': ('django.db.models.fields.DateTimeField', [], {}),
            'plan': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'proration': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'payments.transfer': {
            'Meta': {'object_name': 'Transfer'},
            'adjustment_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'adjustment_fees': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'adjustment_gross': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'charge_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'charge_fees': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'charge_gross': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'collected_fee_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'collected_fee_gross': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '25'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transfers'", 'to': u"orm['payments.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'net': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'refund_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'refund_fees': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'refund_gross': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'validation_count': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'validation_fees': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '9', 'decimal_places': '2'})
        },
        u'payments.transferchargefee': {
            'Meta': {'object_name': 'TransferChargeFee'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'application': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '10'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'transfer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charge_fee_details'", 'to': u"orm['payments.Transfer']"})
        }
    }

    complete_apps = ['payments']