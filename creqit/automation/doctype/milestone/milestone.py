# Copyright (c) 2019, creqit Technologies and contributors
# License: MIT. See LICENSE

import creqit
from creqit.model.document import Document


class Milestone(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from creqit.types import DF

		milestone_tracker: DF.Link | None
		reference_name: DF.Data
		reference_type: DF.Link
		track_field: DF.Data
		value: DF.Data
	# end: auto-generated types

	pass


def on_doctype_update():
	creqit.db.add_index("Milestone", ["reference_type", "reference_name"])
