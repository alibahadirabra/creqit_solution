# Copyright (c) 2019, creqit Technologies and contributors
# License: MIT. See LICENSE

# import creqit
from creqit.model.document import Document


class DashboardChartLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from creqit.types import DF

		chart: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		width: DF.Literal["Half", "Full"]
	# end: auto-generated types

	pass
