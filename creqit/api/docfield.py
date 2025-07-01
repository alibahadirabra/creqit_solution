import creqit
from creqit.model.document import Document

@creqit.whitelist()
def manage_docfield(action, **kwargs):
    try:
        if action not in ["insert", "update", "delete", "get"]:
            return {"status": "error", "message": "Invalid action. Must be 'insert', 'update', 'delete', or 'get'."}

        required_keys = ["parent", "fieldname"]
        for key in required_keys:
            if key not in kwargs:
                creqit.throw(f"{key} is required")

        parent = kwargs.get("parent")
        fieldname = kwargs.get("fieldname")

        if action == "insert":
            # Aynı parent ve fieldname ile kayıt var mı kontrol ediyorum AliBK
            existing = creqit.db.exists("DocField", {"parent": parent, "fieldname": fieldname})
            if existing:
                return {"status": "error", "message": f"Field '{fieldname}' already exists in {parent}."}

            idx = creqit.db.count("DocField", {"parent": parent}) + 1

            doc = creqit.get_doc({
                "doctype": "DocField",
                "parent": parent,
                "parenttype": "DocType",
                "parentfield": "fields",
                "idx": idx
            })

            for column in [
                "fieldname", "label", "oldfieldname", "fieldtype", "oldfieldtype", "options", "search_index",
                "show_dashboard", "hidden", "set_only_once", "allow_in_quick_entry", "print_hide",
                "report_hide", "reqd", "bold", "in_global_search", "collapsible", "unique", "no_copy",
                "allow_on_submit", "show_preview_popup", "trigger", "collapsible_depends_on",
                "mandatory_depends_on", "read_only_depends_on", "depends_on", "permlevel",
                "ignore_user_permissions", "width", "print_width", "columns", "default", "description",
                "in_list_view", "fetch_if_empty", "in_filter", "remember_last_selected_value",
                "ignore_xss_filter", "print_hide_if_no_value", "allow_bulk_edit", "in_standard_filter",
                "in_preview", "read_only", "precision", "max_height", "length", "translatable",
                "hide_border", "hide_days", "hide_seconds", "non_negative", "is_virtual", "not_nullable",
                "sort_options", "link_filters", "fetch_from", "show_on_timeline", "make_attachment_public",
                "documentation_url", "placeholder"
            ]:
                if column in kwargs:
                    value = kwargs[column]
                    try:
                        doc.set(column, int(value) if str(value) in ["0", "1"] else value)
                    except:
                        doc.set(column, value)

            doc.insert(ignore_permissions=True)
            creqit.db.commit() #bu olmazsa işlem başarılı oluyor ama db ye kaydetmiyor temp te kalıyor. AliBK
            creqit.clear_cache(doctype=parent) #Cache temizlemek mevcuttaki değişikliğin yansıması için önemli. AliBK
            return {"status": "success", "message": f"Field '{fieldname}' inserted into {parent}."}

        elif action == "update":
            doc = creqit.get_doc("DocField", {"parent": parent, "fieldname": fieldname})
            for key, val in kwargs.items():
                if hasattr(doc, key):
                    try:
                        doc.set(key, int(val) if str(val) in ["0", "1"] else val)
                    except:
                        doc.set(key, val)
            doc.save(ignore_permissions=True)
            creqit.db.commit()
            creqit.clear_cache(doctype=parent)
            return {"status": "success", "message": f"Field '{fieldname}' updated in {parent}."}

        elif action == "delete":
            doc = creqit.get_doc("DocField", {"parent": parent, "fieldname": fieldname})
            doc.delete(ignore_permissions=True)
            creqit.db.commit()
            creqit.clear_cache(doctype=parent)
            return {"status": "success", "message": f"Field '{fieldname}' deleted from {parent}."}

        elif action == "get":
            doc = creqit.get_doc("DocField", {"parent": parent, "fieldname": fieldname})
            return {"status": "success", "data": doc.as_dict()}

    except Exception as e:
        creqit.log_error(creqit.get_traceback(), "manage_docfield API Error")
        return {"status": "error", "message": str(e)}
