import creqit
from creqit import _

@creqit.whitelist()
def get_contacts_by_company(contact_name=None, company=None):
    if not company:
        return []

    # Yetki kontrolü yapabilirsin burada, örn. sadece System Manager'lar erişsin
    # if not creqit.has_permission("Contact_CRM"):
    #     creqit.throw(_("You are not permitted to access Contact_CRM"))

    contacts = creqit.get_all("Contact_CRM",
        filters={"linkaccount": company},
        fields=["name_surname", "title", "linkaccount", "department", "email", "phone", "mobilephone", "fax", "lastactivity"]
    )
    return contacts
