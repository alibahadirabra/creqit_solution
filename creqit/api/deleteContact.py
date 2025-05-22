
def on_trash(doc, method=None):
    # Diğer doctypelardaki aynı email ve phone'la eşleşenleri sil
    if not (doc.email or doc.phone):
        return

    filters = {"email": doc.email}
    if doc.phone:
        filters["phone"] = doc.phone

    # Leads içinde sil
    leads = creqit.get_all("Leads", filters={}, fields=["name"])
    for lead in leads:
        lead_doc = creqit.get_doc("Leads", lead.name)
        new_table = [
            row for row in lead_doc.table_orgl
            if not (row.email == doc.email and row.phone == doc.phone)
        ]
        if len(new_table) != len(lead_doc.table_orgl):
            lead_doc.table_orgl = new_table
            lead_doc.save()

    # Opportunity içinde sil
    opps = creqit.get_all("Opportunity", filters={}, fields=["name"])
    for opp in opps:
        opp_doc = creqit.get_doc("Opportunity", opp.name)
        new_table = [
            row for row in opp_doc.table_orgl
            if not (row.email == doc.email and row.phone == doc.phone)
        ]
        if len(new_table) != len(opp_doc.table_orgl):
            opp_doc.table_orgl = new_table
            opp_doc.save()
