import frappe
from frappe import _


@frappe.whitelist()
def get_budget_consumed_vs_remaining(filters=None):
	"""Donut: consumed vs remaining, summed across Workforce Plan."""
	filters = _dict(filters)
	rows = frappe.get_list(
		"Workforce Plan",
		filters=filters,
		fields=["sum(consumed_budget) as consumed", "sum(remaining_budget) as remaining"],
	)
	r = rows[0] if rows else {}
	return [
		{"label": _("Consumed"), "value": r.get("consumed") or 0},
		{"label": _("Remaining"), "value": r.get("remaining") or 0},
	]


@frappe.whitelist()
def get_budget_by_department(filters=None):
	"""Approved / committed / consumed budget grouped by Workforce Plan department."""
	filters = _dict(filters)
	rows = frappe.get_list(
		"Workforce Plan",
		filters=filters,
		group_by="department",
		fields=[
			"department as label",
			"sum(approved_budget) as approved",
			"sum(committed_budget) as committed",
			"sum(consumed_budget) as consumed",
		],
		order_by="sum(approved_budget) desc",
	)
	return [
		{
			"label": r.label or _("Unassigned"),
			"approved": r.approved or 0,
			"committed": r.committed or 0,
			"consumed": r.consumed or 0,
		}
		for r in rows
	]


@frappe.whitelist()
def get_budget_by_project(filters=None):
	"""Approved / committed / consumed budget grouped by Workforce Plan project.

	Grouped on custom_project_name (Data, denormalized from custom_project on
	save) rather than the custom_project Link itself, so the chart label is
	already the readable project name with no extra lookup query."""
	filters = _dict(filters)
	rows = frappe.get_list(
		"Workforce Plan",
		filters=filters,
		group_by="custom_project_name",
		fields=[
			"custom_project_name as label",
			"sum(approved_budget) as approved",
			"sum(committed_budget) as committed",
			"sum(consumed_budget) as consumed",
		],
		order_by="sum(approved_budget) desc",
	)
	return [
		{
			"label": r.label or _("Unassigned"),
			"approved": r.approved or 0,
			"committed": r.committed or 0,
			"consumed": r.consumed or 0,
		}
		for r in rows
	]


@frappe.whitelist()
def get_budget_by_vendor(filters=None):
	"""Approved vs consumed cost grouped by vendor (Job Requisition Role)."""
	return _role_breakdown("vendor", _dict(filters))


@frappe.whitelist()
def get_budget_by_position(filters=None):
	"""Approved vs consumed cost grouped by position/designation (Job Requisition Role)."""
	return _role_breakdown("designation", _dict(filters))


@frappe.whitelist()
def get_budget_by_classification(filters=None):
	"""Approved vs consumed cost grouped by role classification (Job Requisition Role)."""
	return _role_breakdown("role_classification", _dict(filters))


def _role_breakdown(group_field, filters):
	"""Shared query for the vendor/position/classification breakdowns.

	Job Requisition Role is a child table, so it isn't reachable through the
	generic group-by/aggregate builder in widgets.py (confirmed empty results
	there for child doctypes) — this joins it to its parent Job Requisition
	for the company/date filters and a status-based approved/consumed split:
	"approved" = every role on a requisition that hasn't been rejected or
	cancelled, "consumed" = roles on requisitions already Filled.
	group_field is always one of a fixed internal set (vendor/designation/
	role_classification), never request input, so it's safe to interpolate.
	"""
	conditions = ["1=1"]
	values = {}
	if filters.get("company"):
		conditions.append("jr.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("from_date") and filters.get("to_date"):
		conditions.append("jr.posting_date between %(from_date)s and %(to_date)s")
		values["from_date"] = filters["from_date"]
		values["to_date"] = filters["to_date"]

	rows = frappe.db.sql(
		f"""
		select
			jrr.{group_field} as label,
			sum(case when jr.status not in ('Rejected', 'Cancelled') then jrr.total_estimated_cost_usd else 0 end) as approved,
			sum(case when jr.status = 'Filled' then jrr.total_estimated_cost_usd else 0 end) as consumed
		from `tabJob Requisition Role` jrr
		inner join `tabJob Requisition` jr on jrr.parent = jr.name
		where {" and ".join(conditions)}
		group by jrr.{group_field}
		order by approved desc
		""",
		values,
		as_dict=True,
	)
	return [
		{"label": r.label or _("Not set"), "approved": r.approved or 0, "consumed": r.consumed or 0}
		for r in rows
	]


@frappe.whitelist()
def get_pending_ledger_postings(filters=None):
	"""Table: Workforce Plans whose consumed budget is ahead of what's been
	posted to the ledger so far.

	Journal Entry has no structured Link back to Workforce Plan — the
	automated monthly payroll-accrual entry only names the plans it covers in
	a free-text user_remark — so custom_last_posted_consumed_budget (bumped
	by that same job each time it posts) is the only clean, queryable
	watermark. pending = consumed_budget - custom_last_posted_consumed_budget.
	"""
	filters = _dict(filters)
	rows = frappe.get_list(
		"Workforce Plan",
		filters=filters,
		fields=[
			"name",
			"department",
			"custom_project_name as project",
			"consumed_budget",
			"custom_last_posted_consumed_budget as last_posted",
		],
		limit_page_length=0,
	)
	out = []
	for r in rows:
		pending = (r.consumed_budget or 0) - (r.last_posted or 0)
		if pending > 0:
			out.append(
				{
					"name": r.name,
					"department": r.department,
					"project": r.project,
					"consumed_budget": r.consumed_budget or 0,
					"last_posted": r.last_posted or 0,
					"pending": pending,
				}
			)
	out.sort(key=lambda x: x["pending"], reverse=True)
	return out


@frappe.whitelist()
def get_pending_ledger_postings_total(filters=None):
	"""Number Card total of get_pending_ledger_postings."""
	rows = get_pending_ledger_postings(filters)
	return {"value": sum(r["pending"] for r in rows)}


@frappe.whitelist()
def get_ledger_postings(filters=None):
	"""Table: most recent Journal Entries, newest first.

	Journal Entry's generic Table dispatch (no fields specified) would only
	return the "name" column — not useful — so this explicitly selects the
	columns worth showing, including user_remark, which today is the only
	place the automated payroll-accrual entry records which Workforce Plans
	it covers."""
	filters = _dict(filters)
	rows = frappe.get_list(
		"Journal Entry",
		filters=filters,
		fields=["name", "posting_date", "voucher_type", "total_debit", "user_remark"],
		order_by="posting_date desc",
		limit_page_length=20,
	)
	for r in rows:
		if r.user_remark and len(r.user_remark) > 120:
			r.user_remark = r.user_remark[:117] + "..."
	return rows


def _dict(filters):
	import json

	if not filters:
		return {}
	if isinstance(filters, dict):
		return filters
	return json.loads(filters)
