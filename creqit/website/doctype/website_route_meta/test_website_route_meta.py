# Copyright (c) 2019, creqit Technologies and Contributors
# License: MIT. See LICENSE
import creqit
from creqit.tests import IntegrationTestCase, UnitTestCase
from creqit.utils import set_request
from creqit.website.serve import get_response

EXTRA_TEST_RECORD_DEPENDENCIES = ["Blog Post"]


class UnitTestWebsiteRouteMeta(UnitTestCase):
	"""
	Unit tests for WebsiteRouteMeta.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestWebsiteRouteMeta(IntegrationTestCase):
	def test_meta_tag_generation(self):
		blogs = creqit.get_all(
			"Blog Post", fields=["name", "route"], filters={"published": 1, "route": ("!=", "")}, limit=1
		)

		blog = blogs[0]

		# create meta tags for this route
		doc = creqit.new_doc("Website Route Meta")
		doc.append("meta_tags", {"key": "type", "value": "blog_post"})
		doc.append("meta_tags", {"key": "og:title", "value": "My Blog"})
		doc.name = blog.route
		doc.insert()

		# set request on this route
		set_request(path=blog.route)
		response = get_response()

		self.assertTrue(response.status_code, 200)

		html = self.normalize_html(response.get_data().decode())

		self.assertIn(self.normalize_html("""<meta name="type" content="blog_post">"""), html)
		self.assertIn(self.normalize_html("""<meta property="og:title" content="My Blog">"""), html)

	def tearDown(self):
		creqit.db.rollback()
