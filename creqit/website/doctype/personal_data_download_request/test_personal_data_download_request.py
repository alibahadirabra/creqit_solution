# Copyright (c) 2019, creqit Technologies and Contributors
# License: MIT. See LICENSE
import json

import creqit
from creqit.contacts.doctype.contact.contact import get_contact_name
from creqit.core.doctype.user.user import create_contact
from creqit.tests import IntegrationTestCase, UnitTestCase
from creqit.website.doctype.personal_data_download_request.personal_data_download_request import (
	get_user_data,
)


class UnitTestPersonalDataDownloadRequest(UnitTestCase):
	"""
	Unit tests for PersonalDataDownloadRequest.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestRequestPersonalData(IntegrationTestCase):
	def setUp(self):
		create_user_if_not_exists(email="test_privacy@example.com")

	def tearDown(self):
		creqit.db.delete("Personal Data Download Request")

	def test_user_data_creation(self):
		user_data = json.loads(get_user_data("test_privacy@example.com"))
		contact_name = get_contact_name("test_privacy@example.com")
		expected_data = {"Contact": creqit.get_all("Contact", {"name": contact_name}, ["*"])}
		expected_data = json.loads(json.dumps(expected_data, default=str))
		self.assertEqual({"Contact": user_data["Contact"]}, expected_data)

	def test_file_and_email_creation(self):
		creqit.set_user("test_privacy@example.com")
		download_request = creqit.get_doc(
			{"doctype": "Personal Data Download Request", "user": "test_privacy@example.com"}
		)
		download_request.save(ignore_permissions=True)

		creqit.set_user("Administrator")

		file_count = creqit.db.count(
			"File",
			{
				"attached_to_doctype": "Personal Data Download Request",
				"attached_to_name": download_request.name,
			},
		)

		self.assertEqual(file_count, 1)

		email_queue = creqit.get_all("Email Queue", fields=["message"], order_by="creation DESC", limit=1)
		self.assertIn(creqit._("Download Your Data"), email_queue[0].message)

		creqit.db.delete("Email Queue")


def create_user_if_not_exists(email, first_name=None):
	creqit.delete_doc_if_exists("User", email)

	user = creqit.get_doc(
		{
			"doctype": "User",
			"user_type": "Website User",
			"email": email,
			"send_welcome_email": 0,
			"first_name": first_name or email.split("@", 1)[0],
			"birth_date": creqit.utils.now_datetime(),
		}
	).insert(ignore_permissions=True)
	create_contact(user=user)
