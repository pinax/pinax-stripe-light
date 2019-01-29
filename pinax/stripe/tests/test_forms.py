import datetime
import json
from base64 import b64decode
from copy import copy

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.utils import timezone

from mock import patch
from stripe.error import InvalidRequestError

from ..forms import (
    AdditionalCustomAccountForm,
    InitialCustomAccountForm,
    extract_ipaddress
)
from ..models import Account


def get_stripe_error(field_name=None, message=None):
    if field_name is None:
        field_name = u"legal_entity[dob][year]"
    if message is None:
        message = u"This value must be greater than 1900 (it currently is '1800')."
    json_body = {
        "error": {
            "type": "invalid_request_error",
            "message": message,
            "param": field_name
        }
    }
    http_body = json.dumps(json_body)
    return InvalidRequestError(
        message,
        field_name,
        http_body=http_body,
        json_body=json_body
    )


def get_image(name=None, _type=None):
    # https://raw.githubusercontent.com/mathiasbynens/small/master/jpeg.jpg
    if _type is None:
        _type = "image/jpeg"
    if name is None:
        name = "random-name.jpg"
    image = b64decode(
        "/9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOC"
        "wkJDRENDg8QEBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQ"
        "EAAD8A0s8g/9k="
    )
    return InMemoryUploadedFile(
        image, None, name, _type, len(image), None
    )


class InitialCustomAccountFormTestCase(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="luke",
            email="luke@example.com"
        )
        self.data = {
            "first_name": "Donkey",
            "last_name": "McGee",
            "dob": "1980-01-01",
            "address_line1": "2993 Steve St",
            "address_city": "Fake Town",
            "address_state": "CA",
            "address_country": "US",
            "address_postal_code": "V5Y3Z9",
            "routing_number": "11000-000",
            "account_number": "12345678900",
            "tos_accepted": "true",
            "currency": "USD"
        }
        self.request = RequestFactory().get("/user/account/create")
        self.request.user = self.user

    def test_conditional_state_field(self):
        form = InitialCustomAccountForm(
            self.data,
            request=self.request,
            country="CA"
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["address_state"][0],
            "Select a valid choice. CA is not one of the available choices."
        )

    def test_fields_needed(self):
        form = InitialCustomAccountForm(
            self.data,
            request=self.request,
            country="CA",
            fields_needed=["legal_entity.verification.document"]
        )
        self.assertTrue("document" in form.fields)

    def test_conditional_currency_field(self):
        data = copy(self.data)
        data["currency"] = "AUD"
        form = InitialCustomAccountForm(
            data,
            request=self.request,
            country="US"
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["currency"][0],
            "Select a valid choice. AUD is not one of the available choices."
        )

    @patch("pinax.stripe.actions.accounts.sync_account_from_stripe_data")
    @patch("stripe.Account.create")
    def test_save(self, create_mock, sync_mock):
        form = InitialCustomAccountForm(
            self.data,
            request=self.request,
            country="US"
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(create_mock.called)
        self.assertTrue(sync_mock.called)

    @patch("pinax.stripe.actions.accounts.sync_account_from_stripe_data")
    @patch("stripe.Account.create")
    def test_save_with_stripe_error(self, create_mock, sync_mock):
        create_mock.side_effect = get_stripe_error()
        form = InitialCustomAccountForm(
            self.data,
            request=self.request,
            country="US"
        )
        self.assertTrue(form.is_valid())
        with self.assertRaises(InvalidRequestError):
            form.save()
        self.assertTrue(create_mock.called)
        self.assertFalse(sync_mock.called)
        self.assertEqual(
            form.errors["dob"],
            [u"This value must be greater than 1900 (it currently is '1800')."]
        )

    @patch("stripe.Account.create")
    def test_save_with_stripe_error_unknown_field(self, create_mock):
        create_mock.side_effect = get_stripe_error(
            field_name="unknown",
            message="Oopsie daisy"
        )
        form = InitialCustomAccountForm(
            self.data,
            request=self.request,
            country="US"
        )
        self.assertTrue(form.is_valid())
        with self.assertRaises(InvalidRequestError):
            form.save()
        self.assertEqual(
            form.non_field_errors()[0],
            "Oopsie daisy"
        )

    @override_settings(DEBUG=True)
    @patch("ipware.ip.get_real_ip")
    @patch("ipware.ip.get_ip")
    def test_extract_ipaddress(self, ip_mock, ip_real_mock):
        # force hit of get_ip when get_real_ip returns None
        ip_real_mock.return_value = None
        ip_mock.return_value = "192.168.0.1"
        ip = extract_ipaddress(self.request)
        self.assertEqual(ip, "192.168.0.1")


class AdditionalCustomAccountFormTestCase(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="luke",
            email="luke@example.com"
        )
        self.data = {
            "first_name": "Donkey",
            "last_name": "McGee",
            "dob": "1980-01-01",
            "personal_id_number": "123123123"
        }
        self.account = Account.objects.create(
            user=self.user,
            stripe_id="acct_123123",
            country="US",
            legal_entity_first_name="Donkey",
            legal_entity_last_name="McGee",
            legal_entity_dob=datetime.datetime(1980, 1, 1),
            type="custom",
            verification_due_by=timezone.now() + datetime.timedelta(days=2),
            verification_fields_needed=["legal_entity.personal_id_number"],
        )

    def test_initial_data_from_account(self):
        form = AdditionalCustomAccountForm(
            account=self.account
        )
        self.assertEqual(
            form.fields["first_name"].initial,
            self.account.legal_entity_first_name
        )
        self.assertEqual(
            form.fields["last_name"].initial,
            self.account.legal_entity_last_name
        )
        self.assertEqual(
            form.fields["dob"].initial,
            self.account.legal_entity_dob
        )

    def test_country_from_account(self):
        form = AdditionalCustomAccountForm(
            account=self.account
        )
        self.assertEqual(
            form.country, self.account.country
        )

    def test_fields_needed_from_account(self):
        form = AdditionalCustomAccountForm(
            account=self.account
        )
        self.assertEqual(
            form.fields_needed, self.account.verification_fields_needed
        )

    def test_dynamic_personal_id_field_added(self):
        form = AdditionalCustomAccountForm(
            account=self.account
        )
        self.assertIn("personal_id_number", form.fields)
        self.assertTrue(
            isinstance(form.fields["personal_id_number"], forms.CharField)
        )

    def test_dynamic_document_field_added(self):
        self.account.verification_fields_needed = [
            "legal_entity.verification.document"
        ]
        form = AdditionalCustomAccountForm(
            account=self.account
        )
        self.assertIn("document", form.fields)
        self.assertTrue(
            isinstance(form.fields["document"], forms.FileField)
        )

    def test_multiple_dynamic_fields_added(self):
        self.account.verification_fields_needed = [
            "legal_entity.verification.document",
            "legal_entity.personal_id_number"
        ]
        form = AdditionalCustomAccountForm(
            account=self.account
        )
        self.assertIn("document", form.fields)
        self.assertTrue(
            isinstance(form.fields["document"], forms.FileField)
        )
        self.assertIn("personal_id_number", form.fields)
        self.assertTrue(
            isinstance(form.fields["personal_id_number"], forms.CharField)
        )

    @override_settings(
        PINAX_STRIPE_DOCUMENT_MAX_SIZE_KB=0
    )
    def test_clean_document_too_large(self):
        self.account.verification_fields_needed = [
            "legal_entity.verification.document"
        ]
        form = AdditionalCustomAccountForm(
            self.data,
            account=self.account,
            files={"document": get_image()}
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["document"],
            [u"Document image is too large (> 0.0 MB)"]
        )

    def test_clean_document_wrong_type(self):
        self.account.verification_fields_needed = [
            "legal_entity.verification.document"
        ]
        form = AdditionalCustomAccountForm(
            self.data,
            account=self.account,
            files={"document": get_image(name="donkey.gif", _type="image/gif")}
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["document"],
            [u"The type of image you supplied is not supported. Please upload a JPG or PNG file."]
        )

    def test_clean_dob_too_old(self):
        data = copy(self.data)
        data["dob"] = "1780-01-01"
        form = AdditionalCustomAccountForm(
            data,
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["dob"],
            [u"This must be greater than 1900-01-01."]
        )

    @patch("pinax.stripe.actions.accounts.sync_account_from_stripe_data")
    @patch("stripe.Account.retrieve")
    @patch("stripe.FileUpload.create")
    def test_save(self, file_upload_mock, retrieve_mock, sync_mock):
        self.account.verification_fields_needed = [
            "legal_entity.personal_id_number"
        ]
        form = AdditionalCustomAccountForm(
            self.data,
            account=self.account
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(
            retrieve_mock.return_value.legal_entity.first_name,
            "Donkey"
        )
        self.assertEqual(
            retrieve_mock.return_value.legal_entity.personal_id_number,
            "123123123"
        )
        self.assertFalse(file_upload_mock.called)

    @patch("pinax.stripe.actions.accounts.sync_account_from_stripe_data")
    @patch("stripe.Account.retrieve")
    @patch("stripe.FileUpload.create")
    def test_save_with_document(self, file_upload_mock, retrieve_mock, sync_mock):
        file_upload_mock.return_value = {"id": 5555}
        self.account.verification_fields_needed = [
            "legal_entity.personal_id_number",
            "legal_entity.verification.document"
        ]
        form = AdditionalCustomAccountForm(
            self.data,
            account=self.account,
            files={"document": get_image()}
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(
            retrieve_mock.return_value.legal_entity.first_name,
            "Donkey"
        )
        self.assertEqual(
            retrieve_mock.return_value.legal_entity.personal_id_number,
            "123123123"
        )
        self.assertTrue(file_upload_mock.called)
        self.assertEqual(
            retrieve_mock.return_value.legal_entity.verification.document,
            file_upload_mock.return_value["id"]
        )

    @patch("pinax.stripe.actions.accounts.sync_account_from_stripe_data")
    @patch("stripe.Account.retrieve")
    @patch("stripe.FileUpload.create")
    def test_save_with_stripe_error(self, file_upload_mock, retrieve_mock, sync_mock):
        retrieve_mock.return_value.save.side_effect = get_stripe_error()
        self.account.verification_fields_needed = [
            "legal_entity.personal_id_number",
            "legal_entity.verification.document"
        ]
        form = AdditionalCustomAccountForm(
            self.data,
            account=self.account,
            files={"document": get_image()}
        )
        self.assertTrue(form.is_valid())
        with self.assertRaises(InvalidRequestError):
            form.save()
        self.assertEqual(
            form.errors["dob"],
            [u"This value must be greater than 1900 (it currently is '1800')."]
        )
