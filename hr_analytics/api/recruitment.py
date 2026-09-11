import frappe
from frappe import _

from hr_analytics.api.workflow import get_workflow_stage_counts


@frappe.whitelist()
def get_candidate_funnel(filters=None):
	"""Job Applicant funnel using your custom_recruitment_status workflow —
	reuses the generic workflow introspector so the stage names always match
	whatever you've actually defined for that workflow."""
	return get_workflow_stage_counts("Job Applicant", filters=_dict(filters))


@frappe.whitelist()
def get_requisition_funnel(filters=None):
	"""Job Requisition approval funnel (native workflow_state)."""
	return get_workflow_stage_counts("Job Requisition", filters=_dict(filters))


@frappe.whitelist()
def get_budget_utilization(filters=None):
	"""Approved vs consumed budget by cost center, from Job Requisition.

	NOTE: in your Custom Field export, custom_approved_budget /
	custom_consumed_budget / custom_remaining_budget are typed as Data, not
	Currency/Float — SQL sum() on a Data column will silently misbehave on
	any row that isn't a clean numeric string. Recommend changing those
	three to Currency (or Float) via Customize Form before relying on this
	widget; this function assumes that fix has been made.
	"""
	filters = _dict(filters)
	rows = frappe.get_list(
		"Job Requisition",
		filters=filters,
		group_by="custom_cost_center",
		fields=[
			"custom_cost_center as cost_center",
			"sum(custom_approved_budget) as approved",
			"sum(custom_consumed_budget) as consumed",
		],
	)
	return [
		{
			"label": r.cost_center or _("Unassigned"),
			"approved": r.approved or 0,
			"consumed": r.consumed or 0,
		}
		for r in rows
	]


@frappe.whitelist()
def get_sourcing_mix(filters=None):
	"""Direct hires vs vendor/agency-sourced, from Employee.custom_vendor."""
	filters = _dict(filters)
	direct_filters = dict(filters, custom_vendor=["is", "not set"])
	vendor_filters = dict(filters, custom_vendor=["is", "set"])
	direct = frappe.db.count("Employee", filters=direct_filters)
	vendor = frappe.db.count("Employee", filters=vendor_filters)
	return [
		{"label": _("Direct"), "value": direct},
		{"label": _("Vendor / agency"), "value": vendor},
	]


@frappe.whitelist()
def get_time_to_fill(filters=None):
	"""Average Time to Fill across filled/closed Job Requisitions (native
	auto-calculated field)."""
	filters = _dict(filters)
	filters["status"] = "Filled"
	rows = frappe.get_list(
		"Job Requisition", filters=filters, fields=["avg(time_to_fill) as avg_days"]
	)
	return {"value": round(rows[0].avg_days or 0, 1)}


def _dict(filters):
	import json

	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	return json.loads(filters)
