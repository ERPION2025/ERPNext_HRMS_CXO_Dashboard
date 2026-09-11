import json

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


@frappe.whitelist()
def get_probation_summary(filters=None):
	filters = _dict(filters)
	today = getdate(nowdate())
	week_ahead = add_days(today, 7)

	base = dict(filters, custom_confirmation_status="Probation")

	on_probation = frappe.db.count("Employee", filters=base)

	due_this_week = frappe.db.count(
		"Employee",
		filters=dict(base, custom_probation_end_date=["between", [today, week_ahead]]),
	)

	overdue = frappe.db.count(
		"Employee",
		filters=dict(base, custom_probation_end_date=["<", today]),
	)

	# Confirmed-this-month uses `modified` as a proxy for confirmation date —
	# there's no dedicated custom_confirmation_date field in your export yet.
	# Add one (set it from the Probation Review workflow's Confirmed
	# transition) for an accurate figure; until then this over-counts any
	# Employee record edited this month for unrelated reasons.
	month_start = today.replace(day=1)
	confirmed_this_month = frappe.db.count(
		"Employee",
		filters=dict(
			filters,
			custom_confirmation_status="Confirmed",
			modified=[">=", month_start],
		),
	)

	return {
		"on_probation": on_probation,
		"due_this_week": due_this_week,
		"overdue": overdue,
		"confirmed_this_month": confirmed_this_month,
	}


@frappe.whitelist()
def get_on_probation_count(filters=None):
	return {"value": get_probation_summary(filters)["on_probation"]}


@frappe.whitelist()
def get_due_this_week_count(filters=None):
	return {"value": get_probation_summary(filters)["due_this_week"]}


@frappe.whitelist()
def get_overdue_count(filters=None):
	return {"value": get_probation_summary(filters)["overdue"]}


@frappe.whitelist()
def get_confirmed_this_month_count(filters=None):
	return {"value": get_probation_summary(filters)["confirmed_this_month"]}


@frappe.whitelist()
def get_confirmation_status_breakdown(filters=None):
	filters = _dict(filters)
	rows = frappe.get_list(
		"Employee",
		filters=filters,
		group_by="custom_confirmation_status",
		fields=["custom_confirmation_status as label", "count(*) as value"],
	)
	return [{"label": r.label or _("Not set"), "value": r.value} for r in rows]


@frappe.whitelist()
def get_upcoming_reviews(filters=None, days=21, limit=10):
	filters = _dict(filters)
	today = getdate(nowdate())
	horizon = add_days(today, int(days))

	rows = frappe.get_list(
		"Employee",
		filters=dict(
			filters,
			custom_confirmation_status="Probation",
			custom_probation_end_date=["<=", horizon],
		),
		fields=["name", "employee_name", "department", "custom_probation_end_date as end_date"],
		order_by="custom_probation_end_date asc",
		limit_page_length=int(limit),
	)

	for r in rows:
		days_left = (getdate(r.end_date) - today).days if r.end_date else None
		r["days_left"] = days_left
		if days_left is None:
			r["status"] = "Unknown"
		elif days_left < 0:
			r["status"] = "Overdue"
		elif days_left <= 7:
			r["status"] = "Due soon"
		else:
			r["status"] = "On track"
	return rows


def _dict(filters):
	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	return json.loads(filters)
