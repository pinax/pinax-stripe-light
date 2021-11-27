from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from ..admin import EventAdmin, EventProcessingExceptionAdmin
from ..models import Event, EventProcessingException


class TestEventProcessingExceptionAdmin(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_no_add_permission(self):
        instance = EventProcessingExceptionAdmin(EventProcessingException, admin.site)
        self.assertFalse(instance.has_add_permission(None))

    def test_no_change_permission(self):
        request = self.factory.post("/admin/")
        instance = EventProcessingExceptionAdmin(EventProcessingException, admin.site)
        self.assertFalse(instance.has_change_permission(request))

    def test_has_change_permission(self):
        request = self.factory.get("/admin/")
        instance = EventProcessingExceptionAdmin(EventProcessingException, admin.site)
        self.assertTrue(instance.has_change_permission(request))

    def test_change_view_title(self):
        request = self.factory.get("/admin/")
        request.user = get_user_model().objects.create_user(
            username="staff",
            email="staff@staff.com",
            is_staff=True,
            is_superuser=True
        )
        event = Event.objects.create(kind="foo", message={}, stripe_id="foo")
        error = EventProcessingException.objects.create(event=event, data={}, message="foo")
        instance = EventProcessingExceptionAdmin(EventProcessingException, admin.site)
        response = instance.change_view(request, str(error.pk))
        self.assertEqual(
            response.context_data["title"],
            "View event processing exception"
        )


class TestEventAdmin(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_no_add_permission(self):
        instance = EventAdmin(Event, admin.site)
        self.assertFalse(instance.has_add_permission(None))

    def test_no_change_permission(self):
        factory = RequestFactory()
        request = factory.post("/admin/")
        instance = EventAdmin(Event, admin.site)
        self.assertFalse(instance.has_change_permission(request))

    def test_has_change_permission(self):
        factory = RequestFactory()
        request = factory.get("/admin/")
        instance = EventAdmin(Event, admin.site)
        self.assertTrue(instance.has_change_permission(request))

    def test_change_view_title(self):
        request = self.factory.get("/admin/")
        request.user = get_user_model().objects.create_user(
            username="staff",
            email="staff@staff.com",
            is_staff=True,
            is_superuser=True
        )
        event = Event.objects.create(kind="foo", message={}, stripe_id="foo")
        instance = EventAdmin(Event, admin.site)
        response = instance.change_view(request, str(event.pk))
        self.assertEqual(
            response.context_data["title"],
            "View event"
        )
