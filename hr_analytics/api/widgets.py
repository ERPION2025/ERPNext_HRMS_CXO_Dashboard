import json

import frappe
from frappe import _

from hr_analytics.api.workflow import get_workflow_stage_counts

AGGREGATE_SQL = {"Count": "count(name)", "Sum": "sum({0})", "Average": "avg({0})"}
# NOTE: "count(name)" not "count(*)" — Frappe's order_by/group_by validator
# (ORDER_GROUP_PATTERN in frappe.model.db_query) whitelists a strict
# character set that excludes "*", so "count(*) desc" in order_by throws
# "Illegal SQL Query". count(name) is equivalent (name is never null) and
# passes validation.


@frappe.whitelist()
def get_screens():
	"""Screens the current user is allowed to see, in sort order."""
	screens = frappe.get_all(
		"Dashboard Screen",
		filters={"is_active": 1},
		fields=["name", "screen_name", "title", "icon", "category", "sort_order"],
		order_by="sort_order asc",
	)
	visible = []
	for s in screens:
		doc = frappe.get_cached_doc("Dashboard Screen", s.name)
		if doc.has_visibility_for():
			visible.append(s)
	return visible


@frappe.whitelist()
def get_widgets_for_screen(screen):
	"""Active widget configs for one screen — the frontend renders each of these."""
	screen_doc = frappe.get_cached_doc("Dashboard Screen", screen)
	if not screen_doc.has_visibility_for():
		frappe.throw(_("Not permitted to view this screen"), frappe.PermissionError)

	return frappe.get_all(
		"Dashboard Widget",
		filters={"screen": screen, "is_active": 1},
		fields=[
			"name",
			"widget_name",
			"widget_type",
			"column_span",
			"description",
			"color_theme",
		],
		order_by="sort_order asc",
	)


@frappe.whitelist()
def get_widget_data(widget, global_filters=None):
	"""Single entrypoint the frontend calls per widget. Dispatches to a custom
	API method when the widget defines one, otherwise runs the generic
	group-by/aggregate builder against the configured doctype."""
	w = frappe.get_cached_doc("Dashboard Widget", widget)
	if not w.is_active:
		frappe.throw(_("This widget is hidden"))

	screen_doc = frappe.get_cached_doc("Dashboard Screen", w.screen)
	if not screen_doc.has_visibility_for():
		frappe.throw(_("Not permitted to view this widget"), frappe.PermissionError)

	if not frappe.has_permission(w.source_doctype, "read"):
		frappe.throw(_("Not permitted to read {0}").format(w.source_doctype), frappe.PermissionError)

	filters = _merge_filters(w.filters, global_filters, w.date_field, w.source_doctype)

	if w.api_override:
		return _call_override(w.api_override, filters)

	if w.widget_type == "Workflow Timeline":
		return get_workflow_stage_counts(w.source_doctype, w.workflow, filters)

	if w.widget_type == "Number Card":
		return {"value": _aggregate(w.source_doctype, filters, w.aggregate_function, w.value_field)}

	if w.widget_type == "Table":
		return frappe.get_list(w.source_doctype, filters=filters, limit_page_length=20, order_by="modified desc")

	return _grouped(w.source_doctype, filters, w.group_by_field, w.aggregate_function, w.value_field)


def _merge_filters(widget_filters_json, global_filters, date_field, source_doctype):
	filters = json.loads(widget_filters_json) if widget_filters_json else {}
	gf = _as_dict(global_filters)
	if gf.get("company") and frappe.get_meta(source_doctype).has_field("company"):
		filters["company"] = gf["company"]
	if date_field and gf.get("from_date") and gf.get("to_date"):
		filters[date_field] = ["between", [gf["from_date"], gf["to_date"]]]
	return filters


def _as_dict(value):
	if not value:
		return {}
	if isinstance(value, dict):
		return value
	try:
		return json.loads(value)
	except Exception:
		return {}


def _aggregate(doctype, filters, aggregate_function, value_field):
	# value_field is validated against the doctype's real meta fields in
	# DashboardWidget.validate() before a widget can be saved, so it's safe
	# to interpolate directly here — it can never be arbitrary user input.
	fn = AGGREGATE_SQL.get(aggregate_function or "Count", "count(name)")
	fn_sql = fn.format(value_field) if "{0}" in fn else fn
	rows = frappe.get_list(doctype, filters=filters, fields=[f"{fn_sql} as value"])
	return rows[0].value if rows else 0


def _grouped(doctype, filters, group_by_field, aggregate_function, value_field):
	fn = AGGREGATE_SQL.get(aggregate_function or "Count", "count(name)")
	fn_sql = fn.format(value_field) if "{0}" in fn else fn
	rows = frappe.get_list(
		doctype,
		filters=filters,
		group_by=group_by_field,
		fields=[f"{group_by_field} as label", f"{fn_sql} as value"],
		order_by=f"{fn_sql} desc",
	)
	return [{"label": r.label or _("Not set"), "value": r.value} for r in rows]


def _call_override(dotted_path, filters):
	method = frappe.get_attr(dotted_path)
	frappe.is_whitelisted(method)
	return method(filters=filters)
