import frappe
from frappe import _


@frappe.whitelist()
def get_workflow_stage_counts(source_doctype, workflow=None, filters=None):
	"""Return the real states of the active Workflow on `source_doctype`
	(in their defined order) with a record count in each — used to draw the
	approval-stage timeline for Job Requisition, Job Applicant, Leave
	Application, Mid-Year Review and Annual Performance Review without
	hardcoding any state names that may differ per company/site."""
	filters = filters or {}

	workflow_name = workflow or frappe.db.get_value(
		"Workflow", {"document_type": source_doctype, "is_active": 1}
	)
	if not workflow_name:
		return {"workflow": None, "states": [], "field": None, "message": _("No active Workflow on {0}").format(source_doctype)}

	workflow_state_field = (
		frappe.db.get_value("Workflow", workflow_name, "workflow_state_field") or "workflow_state"
	)

	states = frappe.get_all(
		"Workflow Document State",
		filters={"parent": workflow_name},
		fields=["state", "idx", "doc_status"],
		order_by="idx asc",
	)

	result = []
	for s in states:
		state_filters = dict(filters)
		state_filters[workflow_state_field] = s.state
		count = frappe.db.count(source_doctype, filters=state_filters)
		result.append({"state": s.state, "count": count})

	return {"workflow": workflow_name, "field": workflow_state_field, "states": result}
