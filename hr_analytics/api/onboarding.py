import json

import frappe


@frappe.whitelist()
def get_handoff_funnel(filters=None):
	"""Job Applicant → Employee handoff, using your custom_employee_created
	and custom_onboarded checkboxes."""
	filters = _dict(filters)
	not_created = frappe.db.count("Job Applicant", filters=dict(filters, custom_employee_created=0))
	created_not_onboarded = frappe.db.count(
		"Job Applicant", filters=dict(filters, custom_employee_created=1, custom_onboarded=0)
	)
	onboarded = frappe.db.count(
		"Job Applicant", filters=dict(filters, custom_employee_created=1, custom_onboarded=1)
	)
	return [
		{"label": "Selected, employee not created", "value": not_created},
		{"label": "Employee created, not onboarded", "value": created_not_onboarded},
		{"label": "Onboarded", "value": onboarded},
	]


@frappe.whitelist()
def get_onboarding_progress(filters=None):
	"""Native Employee Onboarding doctype, grouped by boarding_status."""
	filters = _dict(filters)
	if not frappe.db.exists("DocType", "Employee Onboarding"):
		return []
	rows = frappe.get_list(
		"Employee Onboarding",
		filters=filters,
		group_by="boarding_status",
		fields=["boarding_status as label", "count(*) as value"],
	)
	return [{"label": r.label or "Not set", "value": r.value} for r in rows]


def _dict(filters):
	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	return json.loads(filters)
