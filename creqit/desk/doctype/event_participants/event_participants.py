# Copyright (c) 2018, creqit Technologies and contributors
# License: MIT. See LICENSE
from creqit.model.document import Document


class EventParticipants(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from creqit.types import DF

		email: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reference_docname: DF.DynamicLink
		reference_doctype: DF.Link
	# end: auto-generated types

	pass
