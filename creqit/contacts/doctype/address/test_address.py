# Copyright (c) 2015, creqit Technologies and Contributors
# License: MIT. See LICENSE
from functools import partial

import creqit
from creqit.contacts.doctype.address.address import address_query, get_address_display
from creqit.tests import IntegrationTestCase, UnitTestCase


class UnitTestAddress(UnitTestCase):
	"""
	Unit tests for Address.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestAddress(IntegrationTestCase):
	def test_template_works(self):
		if not creqit.db.exists("Address Template", "India"):
			creqit.get_doc({"doctype": "Address Template", "country": "India", "is_default": 1}).insert()

		if not creqit.db.exists("Address", "_Test Address-Office"):
			creqit.get_doc(
				{
					"address_line1": "_Test Address Line 1",
					"address_title": "_Test Address",
					"address_type": "Office",
					"city": "_Test City",
					"state": "Test State",
					"country": "India",
					"doctype": "Address",
					"is_primary_address": 1,
					"phone": "+91 0000000000",
				}
			).insert()

		address = creqit.get_list("Address")[0].name
		display = get_address_display(creqit.get_doc("Address", address).as_dict())
		self.assertTrue(display)

	def test_address_query(self):
		def query(doctype="Address", txt="", searchfield="name", start=0, page_len=20, filters=None):
			if filters is None:
				filters = {"link_doctype": "User", "link_name": "Administrator"}
			return address_query(doctype, txt, searchfield, start, page_len, filters)

		creqit.get_doc(
			{
				"address_type": "Billing",
				"address_line1": "1",
				"city": "Mumbai",
				"state": "Maharashtra",
				"country": "India",
				"doctype": "Address",
				"links": [
					{
						"link_doctype": "User",
						"link_name": "Administrator",
					}
				],
			}
		).insert()

		self.assertGreaterEqual(len(query(txt="Admin")), 1)
		self.assertEqual(len(query(txt="what_zyx")), 0)
