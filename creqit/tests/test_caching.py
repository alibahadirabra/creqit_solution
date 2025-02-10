import time
from unittest.mock import MagicMock

import creqit
from creqit.core.doctype.doctype.test_doctype import new_doctype
from creqit.tests import IntegrationTestCase
from creqit.tests.test_api import creqitAPITestCase
from creqit.utils.caching import redis_cache, request_cache, site_cache

CACHE_TTL = 4
external_service = MagicMock(return_value=30)
register_with_external_service = MagicMock(return_value=True)


@request_cache
def request_specific_api(a: list | tuple | dict | int, b: int) -> int:
	# API that takes very long to return a result
	todays_value = external_service()
	if not isinstance(a, int | float):
		a = 1
	return a**b * todays_value


@creqit.whitelist(allow_guest=True)
@site_cache
def ping() -> str:
	register_with_external_service(creqit.local.site)
	return creqit.local.site


@creqit.whitelist(allow_guest=True)
@site_cache(ttl=CACHE_TTL)
def ping_with_ttl() -> str:
	register_with_external_service(creqit.local.site)
	return creqit.local.site


class TestCachingUtils(IntegrationTestCase):
	def test_request_cache(self):
		retval = []
		acceptable_args = [
			[1, 2, 3, 4],
			range(10),
			{"abc": "test-key"},
			creqit.get_last_doc("DocType"),
			creqit._dict(),
		]

		def same_output_received():
			return all([x for x in set(retval) if x == retval[0]])

		# ensure that external service was called only once
		# thereby return value of request_specific_api is cached
		retval.extend(request_specific_api(120, 23) for _ in range(5))
		external_service.assert_called_once()
		self.assertTrue(same_output_received())

		# ensure that cache differentiates between int & float
		# types. Giving different return values for both
		retval.append(request_specific_api(120.0, 23))
		self.assertTrue(external_service.call_count, 2)

		# ensure that function is executed when call isn't
		# already cached
		retval.clear()
		for _ in range(10):
			request_specific_api(120, 13)
		self.assertTrue(external_service.call_count, 3)
		self.assertTrue(same_output_received())

		# ensure key generation capacity for different types
		retval.clear()
		for arg in acceptable_args:
			external_service.call_count = 0
			for _ in range(2):
				request_specific_api(arg, 13)
			self.assertTrue(external_service.call_count, 1)
		self.assertTrue(same_output_received())


class TestSiteCache(creqitAPITestCase):
	def test_site_cache(self):
		module = __name__
		api_with_ttl = f"{module}.ping_with_ttl"
		api_without_ttl = f"{module}.ping"

		for _ in range(5):
			self.get(f"/api/method/{api_with_ttl}")
			self.get(f"/api/method/{api_without_ttl}")

		self.assertEqual(register_with_external_service.call_count, 2)
		time.sleep(CACHE_TTL)
		self.get(f"/api/method/{api_with_ttl}")
		self.assertEqual(register_with_external_service.call_count, 3)


class TestRedisCache(creqitAPITestCase):
	def test_redis_cache(self):
		function_call_count = 0

		@redis_cache(ttl=CACHE_TTL)
		def calculate_area(radius: float) -> float:
			nonlocal function_call_count
			function_call_count += 1
			return 3.14 * radius**2

		self.assertEqual(calculate_area(10), 314)
		self.assertEqual(function_call_count, 1)
		self.assertEqual(calculate_area(10), 314)
		self.assertEqual(function_call_count, 1)

		time.sleep(CACHE_TTL * 1.5)
		self.assertEqual(calculate_area(10), 314)
		self.assertEqual(function_call_count, 2)

		calculate_area.clear_cache()
		self.assertEqual(calculate_area(10), 314)
		self.assertEqual(function_call_count, 3)
		calculate_area.clear_cache()

	def test_redis_cache_without_params(self):
		function_call_count = 0

		@redis_cache
		def calculate_area(radius: float) -> float:
			nonlocal function_call_count
			function_call_count += 1
			return 3.14 * radius**2

		calculate_area.clear_cache()
		self.assertEqual(calculate_area(10), 314)
		self.assertEqual(function_call_count, 1)

		calculate_area.clear_cache()
		self.assertEqual(calculate_area(10), 314)
		self.assertEqual(function_call_count, 2)

		calculate_area.clear_cache()

	def test_redis_cache_diff_args(self):
		function_call_count = 0

		@redis_cache(ttl=CACHE_TTL)
		def calculate_area(radius: float) -> float:
			nonlocal function_call_count
			function_call_count += 1
			return 3.14 * radius**2

		self.assertEqual(calculate_area(10), 314)
		self.assertEqual(function_call_count, 1)
		self.assertEqual(calculate_area(100), 31400)
		self.assertEqual(function_call_count, 2)

		self.assertEqual(calculate_area(5), 25 * 3.14)
		self.assertEqual(function_call_count, 3)

		calculate_area(10)
		# from cache now
		self.assertEqual(function_call_count, 3)

		calculate_area(radius=10)
		# args, kwargs are treated differently
		self.assertEqual(function_call_count, 4)

		calculate_area(radius=10)
		# kwargs should hit cache too
		self.assertEqual(function_call_count, 4)

	def test_global_clear_cache(self):
		function_call_count = 0

		@redis_cache()
		def calculate_area(radius: float) -> float:
			nonlocal function_call_count
			function_call_count += 1
			return 3.14 * radius**2

		calculate_area(10)
		calculate_area(10)
		calculate_area(10)
		self.assertEqual(function_call_count, 1)

		# This is supposed to clear cache for the active site
		creqit.clear_cache()
		calculate_area(10)
		self.assertEqual(function_call_count, 2)

	def test_user_cache(self):
		function_call_count = 0
		PI = 3.1415
		ENGINEERING_PI = _E = 3

		@redis_cache(user=True)
		def calculate_area(radius: float) -> float:
			nonlocal function_call_count
			PI_APPROX = ENGINEERING_PI if creqit.session.user == "Engineer" else PI
			function_call_count += 1
			return PI_APPROX * radius**2

		with self.set_user("Engineer"):
			self.assertEqual(calculate_area(1), ENGINEERING_PI)
			self.assertEqual(function_call_count, 1)

		with self.set_user("Mathematician"):
			self.assertEqual(calculate_area(1), PI)
			self.assertEqual(function_call_count, 2)

		with self.set_user("Engineer"):
			self.assertEqual(calculate_area(1), ENGINEERING_PI)
			self.assertEqual(function_call_count, 2)

		with self.set_user("Mathematician"):
			self.assertEqual(calculate_area(1), PI)
			self.assertEqual(function_call_count, 2)


class TestDocumentCache(creqitAPITestCase):
	TEST_DOCTYPE = "User"
	TEST_DOCNAME = "Administrator"
	TEST_FIELD = "middle_name"

	def setUp(self) -> None:
		self.test_value = creqit.generate_hash()

	def test_caching(self):
		creqit.get_cached_doc(self.TEST_DOCTYPE, self.TEST_DOCNAME)

		with self.assertQueryCount(0):
			doc = creqit.get_cached_doc(self.TEST_DOCTYPE, self.TEST_DOCNAME)

		doc.db_set(self.TEST_FIELD, self.test_value)
		new_doc = creqit.get_cached_doc(self.TEST_DOCTYPE, self.TEST_DOCNAME)

		self.assertIsNot(doc, new_doc)  # Shouldn't be same object from creqit.local
		self.assertEqual(new_doc.get(self.TEST_FIELD), self.test_value)  # Cache invalidated and fetched
		creqit.db.rollback()

		doc_after_rollback = creqit.get_cached_doc(self.TEST_DOCTYPE, self.TEST_DOCNAME)
		self.assertIsNot(new_doc, doc_after_rollback)
		# Cache invalidated after rollback
		self.assertNotEqual(doc_after_rollback.get(self.TEST_FIELD), self.test_value)

		with self.assertQueryCount(0):
			creqit.get_cached_doc(self.TEST_DOCTYPE, self.TEST_DOCNAME)

	def test_cache_invalidation_set_value(self):
		doc = creqit.get_cached_doc(self.TEST_DOCTYPE, self.TEST_DOCNAME)

		creqit.db.set_value(
			self.TEST_DOCTYPE,
			{"name": ("like", "%Admin%")},
			self.TEST_FIELD,
			self.test_value,
		)

		new_doc = creqit.get_cached_doc(self.TEST_DOCTYPE, self.TEST_DOCNAME)
		self.assertIsNot(doc, new_doc)
		self.assertEqual(new_doc.get(self.TEST_FIELD), self.test_value)

		with self.assertQueryCount(0):
			creqit.get_cached_doc(self.TEST_DOCTYPE, self.TEST_DOCNAME)


class TestRedisWrapper(creqitAPITestCase):
	def test_delete_keys(self):
		prefix = "test_del_"

		for i in range(5):
			creqit.cache.set_value(f"{prefix}{i}", 1)

		self.assertEqual(len(creqit.cache.get_keys(prefix)), 5)
		creqit.cache.delete_keys(prefix)
		self.assertEqual(len(creqit.cache.get_keys(prefix)), 0)

	def test_hash(self):
		key = "test_hash"

		# Confirm that there's no data initially
		exists = creqit.cache.exists(key)
		self.assertFalse(exists)

		# Insert 5 key-value pairs
		for i in range(5):
			creqit.cache.hset(key, f"key_{i}", f"value_{i}")

		# Check that we have 5 values
		values = creqit.cache.hgetall(key)
		self.assertEqual(len(values), 5)

		# Check that each value matches
		for i in range(5):
			value = creqit.cache.hget(key, f"key_{i}")
			self.assertEqual(value, f"value_{i}")

		# Check the keys themselves
		keys = creqit.cache.hkeys(key)
		for i in range(5):
			self.assertIn(f"key_{i}".encode(), keys)

		# Delete a single key and check that we still have the remaining 4
		creqit.cache.hdel(key, "key_1")
		values = creqit.cache.hgetall(key)
		self.assertEqual(len(values), 4)

		# Delete 2 keys and check that we still have the remaining 2
		creqit.cache.hdel(key, ["key_2", "key_3"])
		values = creqit.cache.hgetall(key)
		self.assertEqual(len(values), 2)

		# Delete the hash itself and confirm that there's no data
		creqit.cache.delete_value(key)
		exists = creqit.cache.exists(key)
		self.assertFalse(exists)

	def test_user_cache_clear(self):
		from creqit.cache_manager import user_cache_keys

		# Set some keys that a user's cache would usually have
		user1 = creqit.utils.random_string(10)
		user2 = creqit.utils.random_string(10)
		for key in user_cache_keys:
			creqit.cache.hset(key, user1, key)
			creqit.cache.hset(key, user2, key)

		creqit.clear_cache(user=user1)

		# Check that the keys for user1 are gone
		for key in set(user_cache_keys) - {"home_page"}:
			self.assertFalse(creqit.cache.hexists(key, user1))
			self.assertTrue(creqit.cache.hexists(key, user2))

	def test_doctype_cache_clear(self):
		from creqit.cache_manager import doctype_cache_keys

		# Set some keys that a user's cache would usually have
		doctype1 = new_doctype(creqit.utils.random_string(10))
		doctype2 = new_doctype(creqit.utils.random_string(10))
		for key in doctype_cache_keys:
			creqit.cache.hset(key, doctype1.name, key)
			creqit.cache.hset(key, doctype2.name, key)

		creqit.clear_cache(doctype=doctype1.name)

		# Check that the keys for doctype1 are gone
		for key in doctype_cache_keys:
			self.assertFalse(creqit.cache.hexists(key, doctype1.name))
			self.assertTrue(creqit.cache.hexists(key, doctype2.name))

	def test_backward_compat_cache(self):
		self.assertEqual(creqit.cache, creqit.cache())
