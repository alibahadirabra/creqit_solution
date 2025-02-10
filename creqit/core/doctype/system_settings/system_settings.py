# Copyright (c) 2015, creqit Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import creqit
from creqit import _
from creqit.model import no_value_fields
from creqit.model.document import Document
from creqit.utils import cint, today


class SystemSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from creqit.types import DF

		allow_consecutive_login_attempts: DF.Int
		allow_error_traceback: DF.Check
		allow_guests_to_upload_files: DF.Check
		allow_login_after_fail: DF.Int
		allow_login_using_mobile_number: DF.Check
		allow_login_using_user_name: DF.Check
		allow_older_web_view_links: DF.Check
		allowed_file_extensions: DF.SmallText | None
		app_name: DF.Data | None
		apply_strict_user_permissions: DF.Check
		attach_view_link: DF.Check
		backup_limit: DF.Int
		bypass_2fa_for_retricted_ip_users: DF.Check
		bypass_restrict_ip_check_if_2fa_enabled: DF.Check
		country: DF.Link | None
		currency_precision: DF.Literal["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
		date_format: DF.Literal[
			"yyyy-mm-dd", "dd-mm-yyyy", "dd/mm/yyyy", "dd.mm.yyyy", "mm/dd/yyyy", "mm-dd-yyyy"
		]
		default_app: DF.Literal[None]
		deny_multiple_sessions: DF.Check
		disable_change_log_notification: DF.Check
		disable_document_sharing: DF.Check
		disable_standard_email_footer: DF.Check
		disable_system_update_notification: DF.Check
		disable_user_pass_login: DF.Check
		document_share_key_expiry: DF.Int
		dormant_days: DF.Int
		email_footer_address: DF.SmallText | None
		email_retry_limit: DF.Int
		enable_onboarding: DF.Check
		enable_password_policy: DF.Check
		enable_scheduler: DF.Check
		enable_telemetry: DF.Check
		enable_two_factor_auth: DF.Check
		encrypt_backup: DF.Check
		first_day_of_the_week: DF.Literal[
			"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
		]
		float_precision: DF.Literal["", "2", "3", "4", "5", "6", "7", "8", "9"]
		force_user_to_reset_password: DF.Int
		force_web_capture_mode_for_uploads: DF.Check
		hide_footer_in_auto_email_reports: DF.Check
		language: DF.Link
		lifespan_qrcode_image: DF.Int
		link_field_results_limit: DF.Int
		login_with_email_link: DF.Check
		login_with_email_link_expiry: DF.Int
		logout_on_password_reset: DF.Check
		max_auto_email_report_per_user: DF.Int
		max_file_size: DF.Int
		minimum_password_score: DF.Literal["2", "3", "4"]
		number_format: DF.Literal[
			"#,###.##",
			"#.###,##",
			"# ###.##",
			"# ###,##",
			"#'###.##",
			"#, ###.##",
			"#,##,###.##",
			"#,###.###",
			"#.###",
			"#,###",
		]
		otp_issuer_name: DF.Data | None
		password_reset_limit: DF.Int
		rate_limit_email_link_login: DF.Int
		reset_password_link_expiry_duration: DF.Duration | None
		reset_password_template: DF.Link | None
		rounding_method: DF.Literal["Banker's Rounding (legacy)", "Banker's Rounding", "Commercial Rounding"]
		session_expiry: DF.Data | None
		setup_complete: DF.Check
		store_attached_pdf_document: DF.Check
		strip_exif_metadata_from_uploaded_images: DF.Check
		time_format: DF.Literal["HH:mm:ss", "HH:mm"]
		time_zone: DF.Literal[None]
		two_factor_method: DF.Literal["OTP App", "SMS", "Email"]
		use_number_format_from_currency: DF.Check
		welcome_email_template: DF.Link | None
	# end: auto-generated types

	def validate(self):
		from creqit.twofactor import toggle_two_factor_auth

		enable_password_policy = cint(self.enable_password_policy)
		minimum_password_score = cint(getattr(self, "minimum_password_score", 0))
		if enable_password_policy and minimum_password_score <= 0:
			creqit.throw(_("Please select Minimum Password Score"))
		elif not enable_password_policy:
			self.minimum_password_score = ""

		if self.session_expiry:
			parts = self.session_expiry.split(":")
			if len(parts) != 2 or not (cint(parts[0]) or cint(parts[1])):
				creqit.throw(_("Session Expiry must be in format {0}").format("hh:mm"))

		if self.enable_two_factor_auth:
			if self.two_factor_method == "SMS":
				if not creqit.db.get_single_value("SMS Settings", "sms_gateway_url"):
					creqit.throw(
						_("Please setup SMS before setting it as an authentication method, via SMS Settings")
					)
			toggle_two_factor_auth(True, roles=["All"])
		else:
			self.bypass_2fa_for_retricted_ip_users = 0
			self.bypass_restrict_ip_check_if_2fa_enabled = 0

		creqit.flags.update_last_reset_password_date = False
		if self.force_user_to_reset_password and not cint(
			creqit.db.get_single_value("System Settings", "force_user_to_reset_password")
		):
			creqit.flags.update_last_reset_password_date = True

		self.validate_user_pass_login()
		self.validate_backup_limit()
		self.validate_file_extensions()

		if not self.link_field_results_limit:
			self.link_field_results_limit = 10

		if self.link_field_results_limit > 50:
			self.link_field_results_limit = 50
			label = _(self.meta.get_label("link_field_results_limit"))
			creqit.msgprint(
				_("{0} can not be more than {1}").format(label, 50), alert=True, indicator="yellow"
			)

	def validate_user_pass_login(self):
		if not self.disable_user_pass_login:
			return

		social_login_enabled = creqit.db.exists("Social Login Key", {"enable_social_login": 1})
		ldap_enabled = creqit.db.get_single_value("LDAP Settings", "enabled")
		login_with_email_link_enabled = creqit.db.get_single_value("System Settings", "login_with_email_link")

		if not (social_login_enabled or ldap_enabled or login_with_email_link_enabled):
			creqit.throw(
				_(
					"Please enable atleast one Social Login Key or LDAP or Login With Email Link before disabling username/password based login."
				)
			)

	def validate_backup_limit(self):
		if not self.backup_limit or self.backup_limit < 1:
			creqit.msgprint(_("Number of backups must be greater than zero."), alert=True)
			self.backup_limit = 1

	def validate_file_extensions(self):
		if not self.allowed_file_extensions:
			return

		self.allowed_file_extensions = "\n".join(
			ext.strip().upper() for ext in self.allowed_file_extensions.strip().splitlines()
		)

	def on_update(self):
		self.set_defaults()

		creqit.cache.delete_value("system_settings")
		creqit.cache.delete_value("time_zone")

		if creqit.flags.update_last_reset_password_date:
			update_last_reset_password_date()

	def set_defaults(self):
		from creqit.translate import set_default_language

		for df in self.meta.get("fields"):
			if df.fieldtype not in no_value_fields and self.has_value_changed(df.fieldname):
				creqit.db.set_default(df.fieldname, self.get(df.fieldname))

		if self.language:
			set_default_language(self.language)


def update_last_reset_password_date():
	creqit.db.sql(
		""" UPDATE `tabUser`
		SET
			last_password_reset_date = %s
		WHERE
			last_password_reset_date is null""",
		today(),
	)


@creqit.whitelist()
def load():
	from creqit.utils.momentjs import get_all_timezones

	if "System Manager" not in creqit.get_roles():
		creqit.throw(_("Not permitted"), creqit.PermissionError)

	all_defaults = creqit.db.get_defaults()
	defaults = {}

	for df in creqit.get_meta("System Settings").get("fields"):
		if df.fieldtype in ("Select", "Data"):
			defaults[df.fieldname] = all_defaults.get(df.fieldname)

	return {"timezones": get_all_timezones(), "defaults": defaults}
