creqit.pages["workflow-builder"].on_page_load = function (wrapper) {
	creqit.ui.make_app_page({
		parent: wrapper,
		title: __("Workflow Builder"),
		single_column: true,
	});

	// hot reload in development
	if (creqit.boot.developer_mode) {
		creqit.hot_update = creqit.hot_update || [];
		creqit.hot_update.push(() => load_workflow_builder(wrapper));
	}
};

creqit.pages["workflow-builder"].on_page_show = function (wrapper) {
	load_workflow_builder(wrapper);
};

function load_workflow_builder(wrapper) {
	let route = creqit.get_route();
	let $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	if (route.length > 1) {
		creqit.require("workflow_builder.bundle.js").then(() => {
			creqit.workflow_builder = new creqit.ui.WorkflowBuilder({
				wrapper: $parent,
				page: wrapper.page,
				workflow: route[1],
			});
		});
	} else {
		let d = new creqit.ui.Dialog({
			title: __("Create or Edit Workflow"),
			fields: [
				{
					label: __("Action"),
					fieldname: "action",
					fieldtype: "Select",
					options: [
						{ label: __("Create New"), value: "Create" },
						{ label: __("Edit Existing"), value: "Edit" },
					],
					change() {
						let action = d.get_value("action");
						d.get_primary_btn().text(action === "Create" ? __("Create") : __("Edit"));
					},
				},
				{
					label: __("Select Document Type"),
					fieldname: "doctype",
					fieldtype: "Link",
					options: "DocType",
					filters: {
						istable: 0,
					},
					reqd: 1,
					default: creqit.route_options ? creqit.route_options.doctype : null,
				},
				{
					label: __("New Workflow Name"),
					fieldname: "workflow_name",
					fieldtype: "Data",
					depends_on: (doc) => doc.action === "Create",
					mandatory_depends_on: (doc) => doc.action === "Create",
				},
				{
					label: __("Select Workflow"),
					fieldname: "workflow",
					fieldtype: "Link",
					options: "Workflow",
					only_select: 1,
					depends_on: (doc) => doc.action === "Edit",
					get_query() {
						return {
							filters: {
								document_type: d.get_value("doctype"),
							},
						};
					},
					mandatory_depends_on: (doc) => doc.action === "Edit",
				},
			],
			primary_action_label: __("Edit"),
			primary_action({ action, doctype, workflow, workflow_name }) {
				if (action === "Edit") {
					creqit.set_route("workflow-builder", workflow);
				} else if (action === "Create") {
					d.get_primary_btn().prop("disabled", true);
					creqit.db
						.insert({
							doctype: "Workflow",
							workflow_name: workflow_name,
							document_type: doctype,
						})
						.then((doc) => {
							creqit.set_route("workflow-builder", doc.name);
						})
						.finally(() => {
							d.get_primary_btn().prop("disabled", false);
						});
				}
			},
		});
		d.set_value("action", "Create");
		d.show();
	}
}
