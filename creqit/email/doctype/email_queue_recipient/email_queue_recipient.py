# Copyright (c) 2015, creqit Technologies and contributors
# License: MIT. See LICENSE

import creqit
from creqit.model.document import Document


class EmailQueueRecipient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from creqit.types import DF

		error: DF.Code | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		recipient: DF.Data | None
		status: DF.Literal["", "Not Sent", "Sent"]
	# end: auto-generated types

	DOCTYPE = "Email Queue Recipient"

	def is_mail_to_be_sent(self):
		return self.status == "Not Sent"

	def is_mail_sent(self):
		return self.status == "Sent"

	def update_db(self, commit=False, **kwargs):
		creqit.db.set_value(self.DOCTYPE, self.name, kwargs)
		if commit:
			creqit.db.commit()


def on_doctype_update():
	"""Index required for log clearing, modified is not indexed on child table by default"""
	creqit.db.add_index("Email Queue Recipient", ["modified"])
