// Copyright (c) 2020, creqit Technologies and contributors
// For license information, please see license.txt

creqit.ui.form.on("Module Profile", {
	refresh: function (frm) {
		if (has_common(creqit.user_roles, ["Administrator", "System Manager"])) {
			if (!frm.module_editor && frm.doc.__onload && frm.doc.__onload.all_modules) {
				const module_area = $(frm.fields_dict.module_html.wrapper);
				frm.module_editor = new creqit.ModuleEditor(frm, module_area);
			}
		}

		if (frm.module_editor) {
			frm.module_editor.show();
		}
	},

	validate: function (frm) {
		if (frm.module_editor) {
			frm.module_editor.set_modules_in_table();
		}
	},
});
