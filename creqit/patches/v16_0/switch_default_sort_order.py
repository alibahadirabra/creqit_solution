import json

import click

import creqit
from creqit.model.utils.user_settings import sync_user_settings
from creqit.patches.v14_0.drop_unused_indexes import drop_index_if_exists


def execute():
	if creqit.db.db_type == "postgres":
		return

	db_tables = creqit.db.get_tables(cached=False)

	doctypes = creqit.get_all(
		"DocType",
		{"is_virtual": 0, "istable": 0},
		pluck="name",
	)

	for doctype in doctypes:
		table = f"tab{doctype}"
		if table not in db_tables:
			continue
		creqit.db.add_index(doctype, ["creation"], index_name="creation")
		click.echo(f"✓ created creation index from {table}")

		# TODO: We might have to re-run this in future after all doctypes have migrated
		if creqit.db.get_value("DocType", doctype, "sort_field") != "modified":
			drop_index_if_exists(table, "modified")

	update_sort_order_in_user_settings()


def update_sort_order_in_user_settings():
	creqit.db.auto_commit_on_many_writes = True
	sync_user_settings()

	user_settings = creqit.db.sql("select user, doctype, data from `__UserSettings`", as_dict=1)

	for setting in user_settings:
		doctype = setting.get("doctype")
		doctype_sort_order = creqit.db.get_value("DocType", doctype, "sort_field") or "creation"
		data = setting.data
		if not data or not doctype:
			continue

		data = json.loads(data)
		for view in ["List", "Gantt", "Kanban", "Calendar", "Image", "Inbox", "Report"]:
			view_settings = data.get(view)
			if (
				view_settings
				and (current_sort_by := view_settings.get("sort_by"))
				and current_sort_by == "modified"
				and doctype_sort_order != "modified"
			):
				view_settings["sort_by"] = "creation"
		creqit.db.sql(
			"update __UserSettings set data=%s where doctype=%s and user=%s",
			(json.dumps(data), setting.doctype, setting.user),
		)
