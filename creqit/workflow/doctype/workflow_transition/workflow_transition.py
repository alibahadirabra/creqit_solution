# Copyright (c) 2015, creqit Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import creqit
from creqit.model.document import Document


class WorkflowTransition(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from creqit.types import DF

		action: DF.Link
		allow_self_approval: DF.Check
		allowed: DF.Link
		condition: DF.Code | None
		next_state: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		state: DF.Link
		workflow_builder_id: DF.Data | None
	# end: auto-generated types

	pass
