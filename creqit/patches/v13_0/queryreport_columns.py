# Copyright (c) 2021, creqit Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json

import creqit


def execute():
	"""Convert Query Report json to support other content."""
	records = creqit.get_all("Report", filters={"json": ["!=", ""]}, fields=["name", "json"])
	for record in records:
		jstr = record["json"]
		data = json.loads(jstr)
		if isinstance(data, list):
			# double escape braces
			jstr = f'{{"columns":{jstr}}}'
			creqit.db.set_value("Report", record["name"], "json", jstr)
