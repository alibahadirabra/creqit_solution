from datetime import timedelta

import creqit
from creqit.tests import IntegrationTestCase
from creqit.utils.data import now_datetime


class TestTestUtils(IntegrationTestCase):
	SHOW_TRANSACTION_COMMIT_WARNINGS = True

	def test_document_assertions(self):
		currency = creqit.new_doc("Currency")
		currency.currency_name = "STONKS"
		currency.smallest_currency_fraction_value = 0.420_001
		currency.save()

		self.assertDocumentEqual(currency.as_dict(), currency)

	def test_thread_locals(self):
		creqit.flags.temp_flag_to_be_discarded = True

	def test_temp_setting_changes(self):
		current_setting = creqit.get_system_settings("logout_on_password_reset")

		with IntegrationTestCase.change_settings(
			"System Settings", {"logout_on_password_reset": int(not current_setting)}
		):
			updated_settings = creqit.get_system_settings("logout_on_password_reset")
			self.assertNotEqual(current_setting, updated_settings)

		restored_settings = creqit.get_system_settings("logout_on_password_reset")
		self.assertEqual(current_setting, restored_settings)

	def test_time_freezing(self):
		now = now_datetime()

		tomorrow = now + timedelta(days=1)
		with self.freeze_time(tomorrow):
			self.assertEqual(now_datetime(), tomorrow)


def tearDownModule():
	"""assertions for ensuring tests didn't leave state behind"""
	assert "temp_flag_to_be_discarded" not in creqit.flags
	assert not creqit.db.exists("Currency", "STONKS")
