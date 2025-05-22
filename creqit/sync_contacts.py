import creqit

def sync_table_orgl(doc, method):
    other_doctype = "Opportunity" if doc.doctype == "Leads" else "Leads"

    if not doc.company:
        return

    # Bu kayda ait email + phone değerlerini al
    current_contacts = {(row.email, row.phone) for row in doc.table_orgl}

    # Diğer Doctype'ta bu şirkete ait kayıtları getir
    other_docs = creqit.get_all(other_doctype, filters={"company": doc.company}, fields=["name"])

    for d in other_docs:
        other_doc = creqit.get_doc(other_doctype, d.name)
        updated = False

        for row in list(other_doc.table_orgl):
            if (row.email, row.phone) not in current_contacts:
                other_doc.remove(row)
                updated = True

        if updated:
            other_doc.save(ignore_permissions=True)
            creqit.db.commit()
