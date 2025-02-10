// Copyright (c) 2016, creqit Technologies and contributors
// For license information, please see license.txt

creqit.ui.form.on("Module Def", {
	refresh: function (frm) {
		creqit.xcall("creqit.core.doctype.module_def.module_def.get_installed_apps").then((r) => {
			frm.set_df_property("app_name", "options", JSON.parse(r));
			if (!frm.doc.app_name) {
				frm.set_value("app_name", "creqit");
			}
		});

		if (!creqit.boot.developer_mode) {
			frm.set_df_property("custom", "read_only", 1);
			if (frm.is_new()) {
				frm.set_value("custom", 1);
			}
		}
	},
});
