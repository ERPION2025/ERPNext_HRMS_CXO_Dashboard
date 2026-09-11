import json

import frappe
from frappe.utils import add_months, getdate, nowdate

from hr_analytics.api.recruitment import get_budget_utilization, get_sourcing_mix


@frappe.whitelist()
def get_headcount(filters=None):
	filters = _dict(filters)
	return {"value": frappe.db.count("Employee", filters=dict(filters, status="Active"))}


@frappe.whitelist()
def get_attrition_rate(filters=None, months=12):
	"""(Employees who left in the trailing window) / (average headcount) * 100."""
	filters = _dict(filters)
	today = getdate(nowdate())
	period_start = add_months(today, -int(months))

	left = frappe.db.count(
		"Employee",
		filters=dict(filters, status="Left", relieving_date=["between", [period_start, today]]),
	)
	avg_headcount = frappe.db.count("Employee", filters=dict(filters, status="Active")) or 1
	return {"value": round((left / avg_headcount) * 100, 1), "left_count": left}


@frappe.whitelist()
def get_confirmation_rate(filters=None):
	filters = _dict(filters)
	confirmed = frappe.db.count("Employee", filters=dict(filters, custom_confirmation_status="Confirmed"))
	total = frappe.db.count(
		"Employee",
		filters=dict(filters, custom_confirmation_status=["in", ["Confirmed", "Probation", "Extended"]]),
	)
	return {"value": round((confirmed / total) * 100, 1) if total else 0}


@frappe.whitelist()
def get_workforce_composition(filters=None):
	return get_sourcing_mix(filters=filters)


@frappe.whitelist()
def get_budget_overview(filters=None):
	rows = get_budget_utilization(filters=filters)
	approved = sum(r["approved"] for r in rows)
	consumed = sum(r["consumed"] for r in rows)
	return {
		"approved": approved,
		"consumed": consumed,
		"utilization_pct": round((consumed / approved) * 100, 1) if approved else 0,
		"by_cost_center": rows,
	}


@frappe.whitelist()
def get_budget_utilization_pct(filters=None):
	return {"value": get_budget_overview(filters)["utilization_pct"]}


def _dict(filters):
	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	return json.loads(filters)
