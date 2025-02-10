# Copyright (c) 2019, creqit Technologies and contributors
# License: MIT. See LICENSE
import creqit
from creqit.tests import IntegrationTestCase, UnitTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = ["User", "Connected App", "Token Cache"]


class UnitTestTokenCache(UnitTestCase):
	"""
	Unit tests for TokenCache.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestTokenCache(IntegrationTestCase):
	def setUp(self):
		self.token_cache = creqit.get_last_doc("Token Cache")
		self.token_cache.update({"connected_app": creqit.get_last_doc("Connected App").name})
		self.token_cache.save(ignore_permissions=True)

	def test_get_auth_header(self):
		self.token_cache.get_auth_header()

	def test_update_data(self):
		self.token_cache.update_data(
			{
				"access_token": "new-access-token",
				"refresh_token": "new-refresh-token",
				"token_type": "bearer",
				"expires_in": 2000,
				"scope": "new scope",
			}
		)

	def test_get_expires_in(self):
		self.token_cache.get_expires_in()

	def test_is_expired(self):
		self.token_cache.is_expired()

	def get_json(self):
		self.token_cache.get_json()
