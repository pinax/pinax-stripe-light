# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from jsonfield.fields import JSONField


class StripeObject(models.Model):

    stripe_id = models.CharField(max_length=191, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class Event(StripeObject):

    kind = models.CharField(max_length=250)
    livemode = models.BooleanField(default=False)
    customer_id = models.CharField(max_length=200, blank=True)
    account_id = models.CharField(max_length=200, blank=True)
    webhook_message = JSONField()
    validated_message = JSONField(null=True, blank=True)
    valid = models.NullBooleanField(null=True, blank=True)
    processed = models.BooleanField(default=False)
    pending_webhooks = models.PositiveIntegerField(default=0)
    api_version = models.CharField(max_length=100, blank=True)

    @property
    def message(self):
        return self.validated_message

    def __str__(self):
        return "{} - {}".format(self.kind, self.stripe_id)

    def __repr__(self):
        return "Event(pk={!r}, kind={!r}, customer={!r}, valid={!r}, created_at={!s}, stripe_id={!r})".format(
            self.pk,
            self.kind,
            self.customer_id,
            self.valid,
            self.created_at.replace(microsecond=0).isoformat(),
            self.stripe_id,
        )


class EventProcessingException(models.Model):

    event = models.ForeignKey("Event", null=True, blank=True, on_delete=models.CASCADE)
    data = models.TextField()
    message = models.CharField(max_length=500)
    traceback = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "<{}, pk={}, Event={}>".format(self.message, self.pk, self.event)
