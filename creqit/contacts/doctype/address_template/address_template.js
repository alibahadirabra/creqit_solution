// Copyright (c) 2016, creqit Technologies and contributors
// For license information, please see license.txt

creqit.ui.form.on("Address Template", {
	refresh: function (frm) {
		if (frm.is_new() && !frm.doc.template) {
			// set default template via js so that it is translated
			creqit.call({
				method: "creqit.contacts.doctype.address_template.address_template.get_default_address_template",
				callback: function (r) {
					frm.set_value("template", r.message);
				},
			});
		}
	},
});
