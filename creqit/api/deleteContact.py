@creqit.whitelist()
def remove_contact_from_all(email, phone=None):
    filters = {"email": email}
    if phone:
        filters["phone"] = phone

    for doctype in ["Leads", "Opportunity"]:
        docs = creqit.get_all(doctype, fields=["name"])
        for doc in docs:
            doc_instance = creqit.get_doc(doctype, doc.name)
            new_rows = []
            changed = False
            for row in doc_instance.table_orgl:
                if row.email == email and (not phone or row.phone == phone):
                    changed = True
                    continue
                new_rows.append(row)
            if changed:
                doc_instance.table_orgl = new_rows
                doc_instance.save()
