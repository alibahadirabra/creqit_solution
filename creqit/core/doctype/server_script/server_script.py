# Copyright (c) 2019, creqit Technologies and contributors
# License: MIT. See LICENSE

from functools import partial
from types import FunctionType, MethodType, ModuleType
from typing import TYPE_CHECKING

import creqit
from creqit import _
from creqit.model.document import Document
from creqit.rate_limiter import rate_limit
from creqit.utils.safe_exec import (
	creqitTransformer,
	NamespaceDict,
	get_safe_globals,
	is_safe_exec_enabled,
	safe_exec,
)

if TYPE_CHECKING:
	from creqit.core.doctype.scheduled_job_type.scheduled_job_type import ScheduledJobType


class ServerScript(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from creqit.types import DF

		allow_guest: DF.Check
		api_method: DF.Data | None
		cron_format: DF.Data | None
		disabled: DF.Check
		doctype_event: DF.Literal[
			"Before Insert",
			"Before Validate",
			"Before Save",
			"After Insert",
			"After Save",
			"Before Rename",
			"After Rename",
			"Before Submit",
			"After Submit",
			"Before Cancel",
			"After Cancel",
			"Before Discard",
			"After Discard",
			"Before Delete",
			"After Delete",
			"Before Save (Submitted Document)",
			"After Save (Submitted Document)",
			"Before Print",
			"On Payment Authorization",
			"On Payment Paid",
			"On Payment Failed",
			"On Payment Charge Processed",
			"On Payment Mandate Charge Processed",
			"On Payment Mandate Acquisition Processed",
		]
		enable_rate_limit: DF.Check
		event_frequency: DF.Literal[
			"All",
			"Hourly",
			"Daily",
			"Weekly",
			"Monthly",
			"Yearly",
			"Hourly Long",
			"Daily Long",
			"Weekly Long",
			"Monthly Long",
			"Cron",
		]
		module: DF.Link | None
		rate_limit_count: DF.Int
		rate_limit_seconds: DF.Int
		reference_doctype: DF.Link | None
		script: DF.Code
		script_type: DF.Literal["DocType Event", "Scheduler Event", "Permission Query", "API"]
	# end: auto-generated types

	def validate(self):
		creqit.only_for("Script Manager", True)
		self.check_if_compilable_in_restricted_context()

	def on_update(self):
		self.sync_scheduled_job_type()

	def clear_cache(self):
		creqit.cache.delete_value("server_script_map")
		return super().clear_cache()

	def on_trash(self):
		creqit.cache.delete_value("server_script_map")
		if self.script_type == "Scheduler Event":
			for job in self.scheduled_jobs:
				scheduled_job_type: "ScheduledJobType" = creqit.get_doc("Scheduled Job Type", job.name)
				scheduled_job_type.stopped = True
				scheduled_job_type.server_script = None
				scheduled_job_type.save()

	def get_code_fields(self):
		return {"script": "py"}

	@property
	def scheduled_jobs(self) -> list[dict[str, str]]:
		return creqit.get_all(
			"Scheduled Job Type",
			filters={"server_script": self.name},
			fields=["name", "stopped"],
		)

	def sync_scheduled_job_type(self):
		"""Create or update Scheduled Job Type documents for Scheduler Event Server Scripts"""

		def get_scheduled_job() -> "ScheduledJobType":
			if scheduled_script := creqit.db.get_value("Scheduled Job Type", {"server_script": self.name}):
				return creqit.get_doc("Scheduled Job Type", scheduled_script)
			else:
				return creqit.get_doc({"doctype": "Scheduled Job Type", "server_script": self.name})

		previous_script_type = self.get_value_before_save("script_type")
		if previous_script_type != self.script_type and previous_script_type == "Scheduler Event":
			get_scheduled_job().update({"stopped": 1}).save()
			return

		if self.script_type != "Scheduler Event" or not (
			self.has_value_changed("event_frequency")
			or self.has_value_changed("cron_format")
			or self.has_value_changed("disabled")
			or self.has_value_changed("script_type")
		):
			return

		get_scheduled_job().update(
			{
				"method": creqit.scrub(f"{self.name}-{self.event_frequency}"),
				"frequency": self.event_frequency,
				"cron_format": self.cron_format,
				"stopped": self.disabled,
			}
		).save()

		creqit.msgprint(_("Scheduled execution for script {0} has updated").format(self.name), alert=True)

	def check_if_compilable_in_restricted_context(self):
		"""Check compilation errors and send them back as warnings."""
		from RestrictedPython import compile_restricted

		try:
			compile_restricted(self.script, policy=creqitTransformer)
		except Exception as e:
			creqit.msgprint(str(e), title=_("Compilation warning"))

	def execute_method(self) -> dict:
		"""Specific to API endpoint Server Scripts.

		Raise:
		        creqit.DoesNotExistError: If self.script_type is not API.
		        creqit.PermissionError: If self.allow_guest is unset for API accessed by Guest user.

		Return:
		        dict: Evaluate self.script with creqit.utils.safe_exec.safe_exec and return the flags set in its safe globals.
		"""

		if self.enable_rate_limit:
			# Wrap in rate limiter, required for specifying custom limits for each script
			# Note that rate limiter works on `cmd` which is script name
			limit = self.rate_limit_count or 5
			seconds = self.rate_limit_seconds or 24 * 60 * 60

			_fn = partial(execute_api_server_script, script=self)
			return rate_limit(limit=limit, seconds=seconds)(_fn)()
		else:
			return execute_api_server_script(self)

	def execute_doc(self, doc: Document):
		"""Specific to Document Event triggered Server Scripts

		Args:
		        doc (Document): Executes script with for a certain document's events
		"""
		safe_exec(
			self.script,
			_locals={"doc": doc},
			restrict_commit_rollback=True,
			script_filename=self.name,
		)

	def execute_scheduled_method(self):
		"""Specific to Scheduled Jobs via Server Scripts

		Raises:
		        creqit.DoesNotExistError: If script type is not a scheduler event
		"""
		if self.script_type != "Scheduler Event":
			raise creqit.DoesNotExistError

		safe_exec(self.script, script_filename=self.name)

	def get_permission_query_conditions(self, user: str) -> list[str]:
		"""Specific to Permission Query Server Scripts.

		Args:
		        user (str): Take user email to execute script and return list of conditions.

		Return:
		        list: Return list of conditions defined by rules in self.script.
		"""
		locals = {"user": user, "conditions": ""}
		safe_exec(self.script, None, locals, script_filename=self.name)
		if locals["conditions"]:
			return locals["conditions"]


@creqit.whitelist()
def get_autocompletion_items():
	"""Generate a list of autocompletion strings from the context dict
	that is used while executing a Server Script.

	e.g., ["creqit.utils.cint", "creqit.get_all", ...]
	"""

	def get_keys(obj):
		out = []
		for key in obj:
			if key.startswith("_"):
				continue
			value = obj[key]
			if isinstance(value, NamespaceDict | dict) and value:
				if key == "form_dict":
					out.append(["form_dict", 7])
					continue
				for subkey, score in get_keys(value):
					fullkey = f"{key}.{subkey}"
					out.append([fullkey, score])
			else:
				if isinstance(value, type) and issubclass(value, Exception):
					score = 0
				elif isinstance(value, ModuleType):
					score = 10
				elif isinstance(value, FunctionType | MethodType):
					score = 9
				elif isinstance(value, type):
					score = 8
				elif isinstance(value, dict):
					score = 7
				else:
					score = 6
				out.append([key, score])
		return out

	items = creqit.cache.get_value("server_script_autocompletion_items")
	if not items:
		items = get_keys(get_safe_globals())
		items = [{"value": d[0], "score": d[1]} for d in items]
		creqit.cache.set_value("server_script_autocompletion_items", items)
	return items


def execute_api_server_script(script: ServerScript, *args, **kwargs):
	# These are only added for compatibility with rate limiter.
	del args
	del kwargs

	if script.script_type != "API":
		raise creqit.DoesNotExistError

	# validate if guest is allowed
	if creqit.session.user == "Guest" and not script.allow_guest:
		raise creqit.PermissionError

	# output can be stored in flags
	_globals, _locals = safe_exec(script.script, script_filename=script.name)

	return _globals.creqit.flags


@creqit.whitelist()
def enabled() -> bool | None:
	if creqit.has_permission("Server Script"):
		return is_safe_exec_enabled()
