# Copyright (c) 2015, creqit Technologies and Contributors
# License: MIT. See LICENSE
import textwrap

import creqit
from creqit.email.doctype.email_queue.email_queue import SendMailContext, get_email_retry_limit
from creqit.tests import IntegrationTestCase, UnitTestCase


class UnitTestEmailQueue(UnitTestCase):
	"""
	Unit tests for EmailQueue.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestEmailQueue(IntegrationTestCase):
	def test_email_queue_deletion_based_on_modified_date(self):
		from creqit.email.doctype.email_queue.email_queue import EmailQueue

		old_record = creqit.get_doc(
			{
				"doctype": "Email Queue",
				"sender": "Test <test@example.com>",
				"show_as_cc": "",
				"message": "Test message",
				"status": "Sent",
				"priority": 1,
				"recipients": [
					{
						"recipient": "test_auth@test.com",
					}
				],
			}
		).insert()

		old_record.creation = "2010-01-01 00:00:01"
		old_record.recipients[0].creation = old_record.creation
		old_record.db_update_all()

		new_record = creqit.copy_doc(old_record)
		new_record.insert()

		EmailQueue.clear_old_logs()

		self.assertFalse(creqit.db.exists("Email Queue", old_record.name))
		self.assertFalse(creqit.db.exists("Email Queue Recipient", {"parent": old_record.name}))

		self.assertTrue(creqit.db.exists("Email Queue", new_record.name))
		self.assertTrue(creqit.db.exists("Email Queue Recipient", {"parent": new_record.name}))

	def test_failed_email_notification(self):
		subject = creqit.generate_hash()
		email_record = creqit.new_doc("Email Queue")
		email_record.sender = "Test <test@example.com>"
		email_record.message = textwrap.dedent(
			f"""\
		MIME-Version: 1.0
		Message-Id: {creqit.generate_hash()}
		X-Original-From: Test <test@example.com>
		Subject: {subject}
		From: Test <test@example.com>
		To: <!--recipient-->
		Date: {creqit.utils.now_datetime().strftime('%a, %d %b %Y %H:%M:%S %z')}
		Reply-To: test@example.com
		X-creqit-Site: {creqit.local.site}
		"""
		)
		email_record.status = "Error"
		email_record.retry = get_email_retry_limit()
		email_record.priority = 1
		email_record.reference_doctype = "User"
		email_record.reference_name = "Administrator"
		email_record.insert()

		# Simulate an exception so that we get a notification
		try:
			with SendMailContext(queue_doc=email_record):
				raise Exception("Test Exception")
		except Exception:
			pass

		notification_log = creqit.db.get_value(
			"Notification Log",
			{"subject": f"Failed to send email with subject: {subject}"},
		)
		self.assertTrue(notification_log)

	def test_perf_reusing_smtp_server(self):
		"""Ensure that same smtpserver instance is being returned when retrieved multiple times."""

		self.assertTrue(creqit.new_doc("Email Queue").get_email_account()._from_site_config)

		def get_server(q):
			return q.get_email_account().get_smtp_server()

		self.assertIs(get_server(creqit.new_doc("Email Queue")), get_server(creqit.new_doc("Email Queue")))

		q1 = creqit.new_doc("Email Queue", email_account="_Test Email Account 1")
		q2 = creqit.new_doc("Email Queue", email_account="_Test Email Account 1")
		self.assertIsNot(get_server(creqit.new_doc("Email Queue")), get_server(q1))
		self.assertIs(get_server(q1), get_server(q2))
