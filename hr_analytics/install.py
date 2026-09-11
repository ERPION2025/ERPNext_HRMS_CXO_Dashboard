import frappe

SCREENS = [
	{"screen_name": "recruitment", "title": "Recruitment", "icon": "ti ti-users", "category": "Recruitment", "sort_order": 1},
	{"screen_name": "onboarding", "title": "Onboarding", "icon": "ti ti-user-plus", "category": "Onboarding", "sort_order": 2},
	{"screen_name": "probation", "title": "Probation & Confirmation", "icon": "ti ti-user-check", "category": "Probation & Confirmation", "sort_order": 3},
	{"screen_name": "leave", "title": "Leave", "icon": "ti ti-calendar-time", "category": "Leave", "sort_order": 4},
	{"screen_name": "appraisal", "title": "Appraisal", "icon": "ti ti-target-arrow", "category": "Appraisal", "sort_order": 5},
	{"screen_name": "executive", "title": "Executive", "icon": "ti ti-chart-pie", "category": "Executive", "sort_order": 6},
]

# Each row: widget_name, screen, widget_type, source_doctype, kwargs
# kwargs may include: filters (dict), group_by_field, aggregate_function,
# value_field, date_field, workflow, api_override, column_span, is_active
WIDGETS = [
	# ---------------- Recruitment ----------------
	("Open job openings", "recruitment", "Number Card", "Job Opening",
		{"filters": {"status": "Open"}}),
	("Total applicants", "recruitment", "Number Card", "Job Applicant",
		{"date_field": "creation"}),
	("Average time to fill", "recruitment", "Number Card", "Job Requisition",
		{"api_override": "hr_analytics.api.recruitment.get_time_to_fill"}),
	("Requisition approval stages", "recruitment", "Workflow Timeline", "Job Requisition",
		{"column_span": "3", "description": "Live from the Job Requisition workflow — states shown are whatever you've defined on site"}),
	("Candidate recruitment stages", "recruitment", "Workflow Timeline", "Job Applicant",
		{"column_span": "3", "description": "Live from the custom_recruitment_status workflow"}),
	("Applicants by source", "recruitment", "Bar Chart", "Job Applicant",
		{"group_by_field": "source"}),
	("Applicants by department", "recruitment", "Bar Chart", "Job Applicant",
		{"group_by_field": "custom_department"}),
	("Sourcing mix: direct vs vendor", "recruitment", "Donut Chart", "Employee",
		{"api_override": "hr_analytics.api.recruitment.get_sourcing_mix"}),
	("Budget: approved vs consumed by cost center", "recruitment", "Bar Chart", "Job Requisition",
		{"column_span": "2", "api_override": "hr_analytics.api.recruitment.get_budget_utilization",
			"description": "Requires custom_approved_budget/custom_consumed_budget to be Currency fields, see api/recruitment.py"}),
	("Requisitions: budgeted vs non-budgeted", "recruitment", "Donut Chart", "Job Requisition",
		{"group_by_field": "custom_budgeted"}),
	("Requisitions by role type", "recruitment", "Bar Chart", "Job Requisition",
		{"group_by_field": "custom_role_type"}),
	("Applicants by employment type", "recruitment", "Bar Chart", "Job Applicant",
		{"group_by_field": "custom_employment_type"}),

	# ---------------- Onboarding ----------------
	("New joiners", "onboarding", "Number Card", "Employee",
		{"filters": {"status": "Active"}, "date_field": "date_of_joining"}),
	("Applicant to employee handoff", "onboarding", "Bar Chart", "Job Applicant",
		{"column_span": "2", "api_override": "hr_analytics.api.onboarding.get_handoff_funnel"}),
	("Employee Onboarding status", "onboarding", "Donut Chart", "Employee Onboarding",
		{"api_override": "hr_analytics.api.onboarding.get_onboarding_progress"}),
	("Joiners by department", "onboarding", "Bar Chart", "Employee",
		{"group_by_field": "department", "date_field": "date_of_joining"}),

	# ---------------- Probation & Confirmation ----------------
	("On probation", "probation", "Number Card", "Employee",
		{"api_override": "hr_analytics.api.probation.get_on_probation_count"}),
	("Due this week", "probation", "Number Card", "Employee",
		{"api_override": "hr_analytics.api.probation.get_due_this_week_count"}),
	("Overdue reviews", "probation", "Number Card", "Employee",
		{"api_override": "hr_analytics.api.probation.get_overdue_count"}),
	("Confirmed this month", "probation", "Number Card", "Employee",
		{"api_override": "hr_analytics.api.probation.get_confirmed_this_month_count",
			"description": "Approximate — based on last-modified date until a confirmation-date field is added, see api/probation.py"}),
	("Confirmation status breakdown", "probation", "Donut Chart", "Employee",
		{"api_override": "hr_analytics.api.probation.get_confirmation_status_breakdown"}),
	("Reviews due soon", "probation", "Table", "Employee",
		{"column_span": "3", "api_override": "hr_analytics.api.probation.get_upcoming_reviews"}),
	("Probation headcount by department", "probation", "Bar Chart", "Employee",
		{"filters": {"custom_confirmation_status": "Probation"}, "group_by_field": "department"}),

	# ---------------- Leave ----------------
	("Pending approvals", "leave", "Number Card", "Leave Application",
		{"api_override": "hr_analytics.api.leave.get_pending_count"}),
	("Awaiting second approval", "leave", "Number Card", "Leave Application",
		{"api_override": "hr_analytics.api.leave.get_awaiting_second_approval_count"}),
	("On leave today", "leave", "Number Card", "Leave Application",
		{"api_override": "hr_analytics.api.leave.get_on_leave_today_count"}),
	("Open leave balance liability (est.)", "leave", "Number Card", "Leave Ledger Entry",
		{"api_override": "hr_analytics.api.leave.get_leave_liability",
			"description": "Directional estimate only — see api/leave.py for assumptions"}),
	("Leave approval stages", "leave", "Workflow Timeline", "Leave Application",
		{"column_span": "3"}),
	("Pending by approval flow", "leave", "Donut Chart", "Leave Application",
		{"api_override": "hr_analytics.api.leave.get_pending_by_flow"}),
	("Leave days used by type", "leave", "Bar Chart", "Leave Application",
		{"column_span": "2", "api_override": "hr_analytics.api.leave.get_leave_usage_by_type"}),

	# ---------------- Appraisal ----------------
	("Mid-Year Review stages", "appraisal", "Workflow Timeline", "Mid-Year Review",
		{"column_span": "3"}),
	("Annual Performance Review stages", "appraisal", "Workflow Timeline", "Annual Performance Review",
		{"column_span": "3"}),
	("Mid-Year completion by department", "appraisal", "Bar Chart", "Mid-Year Review",
		{"api_override": "hr_analytics.api.appraisal.get_midyear_completion_by_department",
			"is_active": 0,
			"description": "Off by default — set the real employee-link fieldname in api/appraisal.py first, then switch on"}),
	("Annual Review completion by department", "appraisal", "Bar Chart", "Annual Performance Review",
		{"api_override": "hr_analytics.api.appraisal.get_annual_completion_by_department",
			"is_active": 0,
			"description": "Off by default — set the real employee-link fieldname in api/appraisal.py first, then switch on"}),

	# ---------------- Executive ----------------
	("Headcount", "executive", "Number Card", "Employee",
		{"api_override": "hr_analytics.api.executive.get_headcount"}),
	("Attrition rate (12mo)", "executive", "Number Card", "Employee",
		{"api_override": "hr_analytics.api.executive.get_attrition_rate"}),
	("Confirmation rate", "executive", "Number Card", "Employee",
		{"api_override": "hr_analytics.api.executive.get_confirmation_rate"}),
	("Budget utilization", "executive", "Number Card", "Job Requisition",
		{"api_override": "hr_analytics.api.executive.get_budget_utilization_pct"}),
	("Workforce composition: direct vs vendor", "executive", "Donut Chart", "Employee",
		{"api_override": "hr_analytics.api.executive.get_workforce_composition"}),
	("Budget vs consumed by cost center", "executive", "Bar Chart", "Job Requisition",
		{"column_span": "2", "api_override": "hr_analytics.api.recruitment.get_budget_utilization"}),
]


def after_install():
	create_screens()
	create_widgets()


def create_screens():
	for s in SCREENS:
		if frappe.db.exists("Dashboard Screen", s["screen_name"]):
			continue
		frappe.get_doc({"doctype": "Dashboard Screen", **s}).insert(ignore_permissions=True)


def create_widgets():
	for idx, (widget_name, screen, widget_type, source_doctype, kwargs) in enumerate(WIDGETS, start=1):
		if frappe.db.exists("Dashboard Widget", {"widget_name": widget_name, "screen": screen}):
			continue
		doc = {
			"doctype": "Dashboard Widget",
			"widget_name": widget_name,
			"screen": screen,
			"widget_type": widget_type,
			"source_doctype": source_doctype,
			"sort_order": idx,
			"is_active": kwargs.get("is_active", 1),
			"aggregate_function": kwargs.get("aggregate_function", "Count"),
			"group_by_field": kwargs.get("group_by_field"),
			"value_field": kwargs.get("value_field"),
			"date_field": kwargs.get("date_field"),
			"workflow": kwargs.get("workflow"),
			"api_override": kwargs.get("api_override"),
			"column_span": kwargs.get("column_span", "1"),
			"description": kwargs.get("description"),
		}
		if kwargs.get("filters"):
			import json

			doc["filters"] = json.dumps(kwargs["filters"])
		try:
			frappe.get_doc(doc).insert(ignore_permissions=True)
		except Exception:
			# Doctype not installed on this site (e.g. Employee Onboarding
			# from a different HRMS version) — skip rather than fail the
			# whole install.
			frappe.log_error(title=f"HR Analytics: could not seed widget '{widget_name}'")
			frappe.db.rollback()
