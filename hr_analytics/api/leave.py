import json

import frappe
from frappe import _

from hr_analytics.api.workflow import get_workflow_stage_counts


@frappe.whitelist()
def get_pending_approvals(filters=None):
	"""Pending Leave Applications, split by your Single-Layer / Multi-Layer
	custom_approval_flow, plus how many of those are specifically waiting on
	the second approval (custom_requires_second_approval)."""
	filters = _dict(filters)
	base = dict(filters, status="Open")

	rows = frappe.get_list(
		"Leave Application",
		filters=base,
		group_by="custom_approval_flow",
		fields=["custom_approval_flow as label", "count(*) as value"],
	)
	awaiting_second = frappe.db.count(
		"Leave Application", filters=dict(base, custom_requires_second_approval=1)
	)
	return {
		"total": sum(r.value for r in rows),
		"by_flow": [{"label": r.label or _("Not set"), "value": r.value} for r in rows],
		"awaiting_second_approval": awaiting_second,
	}


@frappe.whitelist()
def get_leave_workflow(filters=None):
	return get_workflow_stage_counts("Leave Application", filters=_dict(filters))


@frappe.whitelist()
def get_pending_count(filters=None):
	return {"value": get_pending_approvals(filters)["total"]}


@frappe.whitelist()
def get_awaiting_second_approval_count(filters=None):
	return {"value": get_pending_approvals(filters)["awaiting_second_approval"]}


@frappe.whitelist()
def get_pending_by_flow(filters=None):
	return get_pending_approvals(filters)["by_flow"]


@frappe.whitelist()
def get_on_leave_today_count(filters=None):
	filters = _dict(filters)
	from frappe.utils import nowdate

	today = nowdate()
	count = frappe.db.count(
		"Leave Application",
		filters=dict(filters, status="Approved", from_date=["<=", today], to_date=[">=", today]),
	)
	return {"value": count}


@frappe.whitelist()
def get_leave_usage_by_type(filters=None):
	filters = _dict(filters)
	filters["status"] = "Approved"
	rows = frappe.get_list(
		"Leave Application",
		filters=filters,
		group_by="leave_type",
		fields=["leave_type as label", "sum(total_leave_days) as value"],
		order_by="value desc",
	)
	return [{"label": r.label, "value": r.value or 0} for r in rows]


@frappe.whitelist()
def get_leave_liability(filters=None):
	"""Rough open-leave-balance liability = remaining leave balance (from
	Leave Ledger Entry, native to HRMS) x an assumed per-day cost derived
	from Employee.custom_agreed_salary / 30.

	This is a starting approximation, not a payroll-grade number — it
	doesn't account for LWP leave types, notice-period rules, or your
	salon's commission-based pay component. Treat it as directional until
	Finance signs off on the per-day cost basis.
	"""
	filters = _dict(filters)
	balances = frappe.get_list(
		"Leave Ledger Entry",
		filters=dict(filters, is_expired=0, is_lwp=0),
		group_by="employee",
		fields=["employee", "sum(leaves) as balance"],
	)
	if not balances:
		return {"value": 0, "currency": "INR"}

	employees = [b.employee for b in balances]
	salaries = frappe.get_all(
		"Employee", filters={"name": ["in", employees]}, fields=["name", "custom_agreed_salary"]
	)
	salary_map = {s.name: (s.custom_agreed_salary or 0) for s in salaries}

	total = 0
	for b in balances:
		per_day = salary_map.get(b.employee, 0) / 30
		total += (b.balance or 0) * per_day

	return {"value": round(total, 2), "currency": "INR"}


def _dict(filters):
	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	return json.loads(filters)
