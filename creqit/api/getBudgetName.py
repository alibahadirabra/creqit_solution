
import creqit
from creqit import _
@creqit.whitelist()
def get_distinct_budget_names(doctype, txt, searchfield, start, page_len, filters):
    # Create Budget'dan distinct budget_name'leri çekiyoruz
    return creqit.db.sql("""
        SELECT DISTINCT budget_name
        FROM `tabCreate Budget`
        WHERE budget_name LIKE %(txt)s
        ORDER BY budget_name
        LIMIT 20
    """, {"txt": "%" + txt + "%"})