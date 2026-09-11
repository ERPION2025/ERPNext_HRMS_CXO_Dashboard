import json

import frappe

from hr_analytics.api.workflow import get_workflow_stage_counts

# We only have the workflow_state customization for "Mid-Year Review" and
# "Annual Performance Review" from your fields export, not their full field
# list. The two functions below work today (they only need workflow_state).
# get_completion_by_department needs the real fieldnames for "employee" and
# any rating/score field on those doctypes — fill in DOCTYPE_EMPLOYEE_FIELD
# and a rating fieldname once you export or share their DocType JSON.

DOCTYPE_EMPLOYEE_FIELD = {
	"Mid-Year Review": "employee",  # TODO: confirm actual fieldname
	"Annual Performance Review": "employee",  # TODO: confirm actual fieldname
}


@frappe.whitelist()
def get_midyear_review_workflow(filters=None):
	return get_workflow_stage_counts("Mid-Year Review", filters=_dict(filters))


@frappe.whitelist()
def get_annual_review_workflow(filters=None):
	return get_workflow_stage_counts("Annual Performance Review", filters=_dict(filters))


@frappe.whitelist()
def get_completion_by_department(doctype, filters=None):
	"""% of reviews past the last workflow state, grouped by the reviewee's
	department. Requires DOCTYPE_EMPLOYEE_FIELD to point at a real Link
	(Employee) field on `doctype` — update the map above first."""
	filters = _dict(filters)
	employee_field = DOCTYPE_EMPLOYEE_FIELD.get(doctype)
	if not employee_field or not frappe.get_meta(doctype).has_field(employee_field):
		frappe.throw(
			f"Set the correct employee-link fieldname for {doctype} in "
			"hr_analytics/api/appraisal.py::DOCTYPE_EMPLOYEE_FIELD before using this widget."
		)

	states = get_workflow_stage_counts(doctype, filters=filters)
	if not states.get("states"):
		return []
	final_state = states["states"][-1]["state"]

	rows = frappe.db.sql(
		f"""
		select e.department as label,
			sum(case when t.{states['field']} = %(final_state)s then 1 else 0 end) as completed,
			count(*) as total
		from `tab{doctype}` t
		join `tabEmployee` e on e.name = t.{employee_field}
		group by e.department
		""",
		{"final_state": final_state},
		as_dict=True,
	)
	return [
		{"label": r.label or "Unassigned", "value": round((r.completed / r.total) * 100, 1) if r.total else 0}
		for r in rows
	]


@frappe.whitelist()
def get_midyear_completion_by_department(filters=None):
	return get_completion_by_department("Mid-Year Review", filters=filters)


@frappe.whitelist()
def get_annual_completion_by_department(filters=None):
	return get_completion_by_department("Annual Performance Review", filters=filters)


def _dict(filters):
	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	return json.loads(filters)
