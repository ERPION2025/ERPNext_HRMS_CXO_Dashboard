import json

import frappe
from frappe import _
from frappe.model.document import Document


class DashboardWidget(Document):
	def validate(self):
		self.validate_filters()
		if not self.api_override:
			self.validate_fieldnames()
		self.validate_workflow()

	def validate_filters(self):
		if not self.filters:
			return
		try:
			parsed = json.loads(self.filters)
		except Exception:
			frappe.throw(_("Filters must be valid JSON, e.g. {{\"status\": \"Open\"}}"))
			return
		if not isinstance(parsed, dict):
			frappe.throw(_("Filters JSON must be an object, e.g. {{\"status\": \"Open\"}}"))

	def validate_fieldnames(self):
		if not self.source_doctype:
			return
		meta = frappe.get_meta(self.source_doctype)

		for fieldname_field in ("group_by_field", "value_field", "date_field"):
			fieldname = self.get(fieldname_field)
			if not fieldname:
				continue
			# allow a few virtual/standard fields that aren't in meta.fields
			if fieldname in ("name", "creation", "modified", "owner", "modified_by"):
				continue
			if not meta.get_field(fieldname):
				frappe.throw(
					_("{0} is not a field on {1}. Check the exact fieldname in the DocType.").format(
						frappe.bold(fieldname), frappe.bold(self.source_doctype)
					)
				)

	def validate_workflow(self):
		if self.widget_type != "Workflow Timeline":
			return
		if self.workflow:
			doctype_on_workflow = frappe.db.get_value("Workflow", self.workflow, "document_type")
			if doctype_on_workflow and self.source_doctype and doctype_on_workflow != self.source_doctype:
				frappe.throw(
					_("Workflow {0} is not defined on {1}").format(self.workflow, self.source_doctype)
				)
