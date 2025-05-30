# Copyright (c) 2021, creqit Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE

from random import choice
from unittest.mock import MagicMock, PropertyMock, patch

import creqit
from creqit.email.doctype.newsletter.exceptions import (
	NewsletterAlreadySentError,
	NoRecipientFoundError,
)
from creqit.email.doctype.newsletter.newsletter import (
	Newsletter,
	confirmed_unsubscribe,
	send_scheduled_email,
)
from creqit.email.queue import flush
from creqit.tests import IntegrationTestCase
from creqit.utils import add_days, getdate

emails = [
	"test_subscriber1@example.com",
	"test_subscriber2@example.com",
	"test_subscriber3@example.com",
	"test1@example.com",
]
newsletters = []


def get_dotted_path(obj: type) -> str:
	klass = obj.__class__
	module = klass.__module__
	if module == "builtins":
		return klass.__qualname__  # avoid outputs like 'builtins.str'
	return f"{module}.{klass.__qualname__}"


class TestNewsletterMixin:
	def setUp(self):
		creqit.set_user("Administrator")
		self.setup_email_group()

	def tearDown(self):
		creqit.set_user("Administrator")
		for newsletter in newsletters:
			creqit.db.delete(
				"Email Queue",
				{
					"reference_doctype": "Newsletter",
					"reference_name": newsletter,
				},
			)
			creqit.delete_doc("Newsletter", newsletter)
			creqit.db.delete("Newsletter Email Group", {"parent": newsletter})
			newsletters.remove(newsletter)

	def setup_email_group(self):
		if not creqit.db.exists("Email Group", "_Test Email Group"):
			creqit.get_doc({"doctype": "Email Group", "title": "_Test Email Group"}).insert()

		for email in emails:
			doctype = "Email Group Member"
			email_filters = {"email": email, "email_group": "_Test Email Group"}

			savepoint = "setup_email_group"
			creqit.db.savepoint(savepoint)

			try:
				creqit.get_doc(
					{
						"doctype": doctype,
						**email_filters,
					}
				).insert(ignore_if_duplicate=True)
			except Exception:
				creqit.db.rollback(save_point=savepoint)
				creqit.db.set_value(doctype, email_filters, "unsubscribed", 0)

			creqit.db.release_savepoint(savepoint)

	def send_newsletter(self, published=0, schedule_send=None) -> str | None:
		creqit.db.delete("Email Queue")
		creqit.db.delete("Email Queue Recipient")
		creqit.db.delete("Newsletter")

		newsletter_options = {
			"published": published,
			"schedule_sending": bool(schedule_send),
			"schedule_send": schedule_send,
		}
		newsletter = self.get_newsletter(**newsletter_options)

		if schedule_send:
			send_scheduled_email()
		else:
			newsletter.send_emails()
			return newsletter.name

		return newsletter

	@staticmethod
	def get_newsletter(**kwargs) -> "Newsletter":
		"""Generate and return Newsletter object"""
		doctype = "Newsletter"
		newsletter_content = {
			"subject": "_Test Newsletter",
			"sender_name": "Test Sender",
			"sender_email": "test_sender@example.com",
			"content_type": "Rich Text",
			"message": "Testing my news.",
		}
		similar_newsletters = creqit.get_all(doctype, newsletter_content, pluck="name")

		for similar_newsletter in similar_newsletters:
			creqit.delete_doc(doctype, similar_newsletter)

		newsletter = creqit.get_doc({"doctype": doctype, **newsletter_content, **kwargs})
		newsletter.append("email_group", {"email_group": "_Test Email Group"})
		newsletter.save(ignore_permissions=True)
		newsletter.reload()
		newsletters.append(newsletter.name)

		attached_files = creqit.get_all(
			"File",
			{
				"attached_to_doctype": newsletter.doctype,
				"attached_to_name": newsletter.name,
			},
			pluck="name",
		)
		for file in attached_files:
			creqit.delete_doc("File", file)

		return newsletter


class TestNewsletter(TestNewsletterMixin, IntegrationTestCase):
	def test_send(self):
		self.send_newsletter()

		email_queue_list = [creqit.get_doc("Email Queue", e.name) for e in creqit.get_all("Email Queue")]
		self.assertEqual(len(email_queue_list), 4)

		recipients = {e.recipients[0].recipient for e in email_queue_list}
		self.assertTrue(set(emails).issubset(recipients))

	def test_unsubscribe(self):
		name = self.send_newsletter()
		to_unsubscribe = choice(emails)
		group = creqit.get_all("Newsletter Email Group", filters={"parent": name}, fields=["email_group"])

		flush()
		confirmed_unsubscribe(to_unsubscribe, group[0].email_group)

		name = self.send_newsletter()
		email_queue_list = [creqit.get_doc("Email Queue", e.name) for e in creqit.get_all("Email Queue")]
		self.assertEqual(len(email_queue_list), 3)
		recipients = [e.recipients[0].recipient for e in email_queue_list]

		for email in emails:
			if email != to_unsubscribe:
				self.assertTrue(email in recipients)

	def test_schedule_send(self):
		newsletter = self.send_newsletter(schedule_send=add_days(getdate(), 1))
		newsletter.db_set("schedule_send", add_days(getdate(), -1))  # Set date in past
		send_scheduled_email()

		email_queue_list = [creqit.get_doc("Email Queue", e.name) for e in creqit.get_all("Email Queue")]
		self.assertEqual(len(email_queue_list), 4)
		recipients = [e.recipients[0].recipient for e in email_queue_list]
		for email in emails:
			self.assertTrue(email in recipients)

	def test_newsletter_send_test_email(self):
		"""Test "Send Test Email" functionality of Newsletter"""
		newsletter = self.get_newsletter()
		test_email = choice(emails)
		newsletter.send_test_email(test_email)

		self.assertFalse(newsletter.email_sent)
		newsletter.save = MagicMock()
		self.assertFalse(newsletter.save.called)
		# check if the test email is in the queue
		email_queue = creqit.get_all(
			"Email Queue",
			filters=[
				["reference_doctype", "=", "Newsletter"],
				["reference_name", "=", newsletter.name],
				["Email Queue Recipient", "recipient", "=", test_email],
			],
		)
		self.assertTrue(email_queue)

	def test_newsletter_status(self):
		"""Test for Newsletter's stats on onload event"""
		newsletter = self.get_newsletter()
		newsletter.email_sent = True
		result = newsletter.get_sending_status()
		self.assertTrue("total" in result)
		self.assertTrue("sent" in result)

	def test_already_sent_newsletter(self):
		newsletter = self.get_newsletter()
		newsletter.send_emails()

		with self.assertRaises(NewsletterAlreadySentError):
			newsletter.send_emails()

	def test_newsletter_with_no_recipient(self):
		newsletter = self.get_newsletter()
		property_path = f"{get_dotted_path(newsletter)}.newsletter_recipients"

		with patch(property_path, new_callable=PropertyMock) as mock_newsletter_recipients:
			mock_newsletter_recipients.return_value = []
			with self.assertRaises(NoRecipientFoundError):
				newsletter.send_emails()

	def test_send_scheduled_email_error_handling(self):
		newsletter = self.get_newsletter(schedule_send=add_days(getdate(), -1))
		job_path = "creqit.email.doctype.newsletter.newsletter.Newsletter.queue_all"
		m = MagicMock(side_effect=creqit.OutgoingEmailError)

		with self.assertRaises(creqit.OutgoingEmailError):
			with patch(job_path, new_callable=m):
				send_scheduled_email()

		newsletter.reload()
		self.assertEqual(newsletter.email_sent, 0)

	def test_retry_partially_sent_newsletter(self):
		creqit.db.delete("Email Queue")
		creqit.db.delete("Email Queue Recipient")
		creqit.db.delete("Newsletter")

		newsletter = self.get_newsletter()
		newsletter.send_emails()
		email_queue_list = [creqit.get_doc("Email Queue", e.name) for e in creqit.get_all("Email Queue")]
		self.assertEqual(len(email_queue_list), 4)

		# delete a queue document to emulate partial send
		queue_recipient_name = email_queue_list[0].recipients[0].recipient
		email_queue_list[0].delete()
		newsletter.email_sent = False

		# make sure the pending recipient is only the one which has been deleted
		self.assertEqual(newsletter.get_pending_recipients(), [queue_recipient_name])

		# retry
		newsletter.send_emails()
		self.assertEqual(creqit.db.count("Email Queue"), 4)
		self.assertTrue(newsletter.email_sent)
