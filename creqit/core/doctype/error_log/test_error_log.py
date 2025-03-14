# Copyright (c) 2015, creqit Technologies and Contributors
# License: MIT. See LICENSE
from unittest.mock import patch

from ldap3.core.exceptions import LDAPException, LDAPInappropriateAuthenticationResult

import creqit
from creqit.tests import IntegrationTestCase, UnitTestCase
from creqit.utils.error import _is_ldap_exception, guess_exception_source


class UnitTestErrorLog(UnitTestCase):
	"""
	Unit tests for ErrorLog.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestErrorLog(IntegrationTestCase):
	def test_error_log(self):
		"""let's do an error log on error log?"""
		doc = creqit.new_doc("Error Log")
		error = doc.log_error("This is an error")
		self.assertEqual(error.doctype, "Error Log")

	def test_ldap_exceptions(self):
		exc = [LDAPException, LDAPInappropriateAuthenticationResult]

		for e in exc:
			self.assertTrue(_is_ldap_exception(e()))


_RAW_EXC = """
   File "apps/creqit/creqit/model/document.py", line 1284, in runner
     add_to_return_value(self, fn(self, *args, **kwargs))
                               ^^^^^^^^^^^^^^^^^^^^^^^^^
   File "apps/creqit/creqit/model/document.py", line 933, in fn
     return method_object(*args, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "apps/creqit/creqit/selling/doctype/sales_order/sales_order.py", line 58, in onload
     raise Exception("what")
 Exception: what
"""

_THROW_EXC = """
   File "apps/creqit/creqit/model/document.py", line 933, in fn
     return method_object(*args, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "apps/creqit/creqit/selling/doctype/sales_order/sales_order.py", line 58, in onload
     creqit.throw("what")
   File "apps/creqit/creqit/__init__.py", line 550, in throw
     msgprint(
   File "apps/creqit/creqit/__init__.py", line 518, in msgprint
     _raise_exception()
   File "apps/creqit/creqit/__init__.py", line 467, in _raise_exception
     raise raise_exception(msg)
 creqit.exceptions.ValidationError: what
"""

TEST_EXCEPTIONS = (
	(
		"creqit (app)",
		_RAW_EXC,
	),
	(
		"creqit (app)",
		_THROW_EXC,
	),
)


class TestExceptionSourceGuessing(IntegrationTestCase):
	@patch.object(creqit, "get_installed_apps", return_value=["creqit", "creqit", "3pa"])
	def test_exc_source_guessing(self, _installed_apps):
		for source, exc in TEST_EXCEPTIONS:
			result = guess_exception_source(exc)
			self.assertEqual(result, source)
