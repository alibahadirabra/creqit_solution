# Copyright (c) 2017, creqit Technologies and Contributors
# License: MIT. See LICENSE
from unittest.mock import MagicMock, patch

from rauth import OAuth2Service

import creqit
from creqit.auth import CookieManager, LoginManager
from creqit.integrations.doctype.social_login_key.social_login_key import BaseUrlNotSetError
from creqit.tests import IntegrationTestCase, UnitTestCase
from creqit.utils import set_request
from creqit.utils.oauth import login_via_oauth2

TEST_GITHUB_USER = "githublogin@example.com"


class UnitTestSocialLoginKey(UnitTestCase):
	"""
	Unit tests for SocialLoginKey.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestSocialLoginKey(IntegrationTestCase):
	def setUp(self) -> None:
		creqit.set_user("Administrator")
		creqit.delete_doc("User", TEST_GITHUB_USER, force=True)
		super().setUp()
		creqit.set_user("Guest")

	def test_adding_creqit_social_login_provider(self):
		creqit.set_user("Administrator")
		provider_name = "creqit"
		social_login_key = make_social_login_key(social_login_provider=provider_name)
		social_login_key.get_social_login_provider(provider_name, initialize=True)
		self.assertRaises(BaseUrlNotSetError, social_login_key.insert)

	def test_github_login_with_private_email(self):
		github_social_login_setup()

		mock_session = MagicMock()
		mock_session.get.side_effect = github_response_for_private_email

		with patch.object(OAuth2Service, "get_auth_session", return_value=mock_session):
			login_via_oauth2("github", "iwriu", {"token": "ewrwerwer"})  # Dummy code and state token

	def test_github_login_with_public_email(self):
		github_social_login_setup()

		mock_session = MagicMock()
		mock_session.get.side_effect = github_response_for_public_email

		with patch.object(OAuth2Service, "get_auth_session", return_value=mock_session):
			login_via_oauth2("github", "iwriu", {"token": "ewrwerwer"})  # Dummy code and state token

	def test_normal_signup_and_github_login(self):
		github_social_login_setup()

		if not creqit.db.exists("User", TEST_GITHUB_USER):
			user = creqit.new_doc("User", email=TEST_GITHUB_USER, first_name="GitHub Login")
			user.insert(ignore_permissions=True)

		mock_session = MagicMock()
		mock_session.get.side_effect = github_response_for_login

		with patch.object(OAuth2Service, "get_auth_session", return_value=mock_session):
			login_via_oauth2("github", "iwriu", {"token": "ewrwerwer"})
		self.assertEqual(creqit.session.user, TEST_GITHUB_USER)

	def test_force_disabled_signups(self):
		key = github_social_login_setup()
		key.sign_ups = "Deny"
		key.save(ignore_permissions=True)

		mock_session = MagicMock()
		mock_session.get.side_effect = github_response_for_login

		with patch.object(OAuth2Service, "get_auth_session", return_value=mock_session):
			login_via_oauth2("github", "iwriu", {"token": "ewrwerwer"})
		self.assertEqual(creqit.session.user, "Guest")

	@IntegrationTestCase.change_settings("Website Settings", disable_signup=1)
	def test_force_enabled_signups(self):
		"""Social login key can override website settings for disabled signups."""
		key = github_social_login_setup()
		key.sign_ups = "Allow"
		key.save(ignore_permissions=True)

		mock_session = MagicMock()
		mock_session.get.side_effect = github_response_for_login

		with patch.object(OAuth2Service, "get_auth_session", return_value=mock_session):
			login_via_oauth2("github", "iwriu", {"token": "ewrwerwer"})

		self.assertEqual(creqit.session.user, TEST_GITHUB_USER)


def make_social_login_key(**kwargs):
	kwargs["doctype"] = "Social Login Key"
	if "provider_name" not in kwargs:
		kwargs["provider_name"] = "Test OAuth2 Provider"
	return creqit.get_doc(kwargs)


def create_or_update_social_login_key():
	# used in other tests (connected app, oauth20)
	try:
		social_login_key = creqit.get_doc("Social Login Key", "creqit")
	except creqit.DoesNotExistError:
		social_login_key = creqit.new_doc("Social Login Key")
	social_login_key.get_social_login_provider("creqit", initialize=True)
	social_login_key.base_url = creqit.utils.get_url()
	social_login_key.enable_social_login = 0
	social_login_key.save()
	creqit.db.commit()

	return social_login_key


def create_github_social_login_key():
	if creqit.db.exists("Social Login Key", "github"):
		return creqit.get_doc("Social Login Key", "github")
	else:
		provider_name = "GitHub"
		social_login_key = make_social_login_key(social_login_provider=provider_name)
		social_login_key.get_social_login_provider(provider_name, initialize=True)

		social_login_key.client_id = "h6htd6q"
		social_login_key.client_secret = "keoererk988ekkhf8w9e8ewrjhhkjer9889"
		social_login_key.insert(ignore_permissions=True)
		return social_login_key


def github_response_for_private_email(url, *args, **kwargs):
	if url == "user":
		return_value = {
			"login": "dummy_username",
			"id": "223342",
			"email": None,
			"first_name": "Github Private",
		}
	else:
		return_value = [{"email": "github@example.com", "primary": True, "verified": True}]

	return MagicMock(status_code=200, json=MagicMock(return_value=return_value))


def github_response_for_public_email(url, *args, **kwargs):
	if url == "user":
		return_value = {
			"login": "dummy_username",
			"id": "223343",
			"email": "github_public@example.com",
			"first_name": "Github Public",
		}

	return MagicMock(status_code=200, json=MagicMock(return_value=return_value))


def github_response_for_login(url, *args, **kwargs):
	if url == "user":
		return_value = {
			"login": "dummy_username",
			"id": "223346",
			"email": None,
			"first_name": "Github Login",
		}
	else:
		return_value = [{"email": TEST_GITHUB_USER, "primary": True, "verified": True}]

	return MagicMock(status_code=200, json=MagicMock(return_value=return_value))


def github_social_login_setup():
	set_request(path="/random")
	creqit.local.cookie_manager = CookieManager()
	creqit.local.login_manager = LoginManager()

	return create_github_social_login_key()
