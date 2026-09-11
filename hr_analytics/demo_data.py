"""Best-effort sample data for trying out the HR Analytics dashboard on a
local/test site. Not part of after_install — run it explicitly:

	bench --site <your-site> execute hr_analytics.demo_data.create_demo_data

It only touches standard HRMS fields plus the custom_* fields this app
reads (see README), and checks each one exists on the site's actual schema
(frappe.get_meta(...).has_field) before setting it — so it degrades
gracefully instead of failing outright on a site whose customizations
differ. Each record is created in its own try/except, same pattern as
install.py's widget seeding, so one bad record never blocks the rest.
Safe to re-run: names are deterministic (HRA-DEMO-* / demo-* prefixes) and
existing records are skipped.
"""

import random

import frappe
from frappe.utils import add_days, add_months, getdate, nowdate

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Human Resources", "Finance"]
DESIGNATIONS = ["Software Engineer", "Sales Executive", "Marketing Manager", "HR Executive", "Accountant"]
FIRST_NAMES = ["Aarav", "Vivaan", "Diya", "Ananya", "Kabir", "Ishaan", "Myra", "Saanvi", "Arjun", "Zara",
	"Reyansh", "Anika", "Vihaan", "Riya", "Advait", "Pari", "Kiaan", "Navya", "Shaurya", "Aditi"]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Nair", "Gupta", "Rao", "Mehta", "Khan", "Reddy", "Joshi"]


def create_demo_data(count=15):
	count = int(count)
	company = _get_company()
	if not company:
		frappe.throw("Create at least one Company before seeding demo data.")

	employees = _create_employees(company, count)
	_create_job_openings(company, 5)
	_create_job_requisitions(company, 5)
	_create_job_applicants(10)
	_create_leave_applications(employees)

	frappe.db.commit()
	print(f"HR Analytics demo data seeded for company '{company}'. Open /app/hr-dashboard to view it.")


def _get_company():
	default = frappe.defaults.get_default("company")
	if default:
		return default
	companies = frappe.get_all("Company", limit=1, pluck="name")
	return companies[0] if companies else None


def _has_field(doctype, fieldname):
	return bool(frappe.get_meta(doctype).has_field(fieldname))


def _set_if_field(doc_dict, doctype, fieldname, value):
	if _has_field(doctype, fieldname):
		doc_dict[fieldname] = value


def _create_employees(company, count):
	created = []
	statuses = (
		["Probation"] * 4
		+ ["Confirmed"] * 4
		+ ["Extended"]
	) if _has_field("Employee", "custom_confirmation_status") else []

	for i in range(count):
		employee_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
		joining_days_ago = random.randint(5, 500)
		date_of_joining = add_days(nowdate(), -joining_days_ago)

		emp = {
			"doctype": "Employee",
			"employee_name": employee_name,
			"first_name": employee_name.split(" ")[0],
			"last_name": employee_name.split(" ")[-1],
			"company": company,
			"gender": random.choice(["Male", "Female"]),
			"date_of_birth": add_days(nowdate(), -random.randint(9000, 16000)),
			"date_of_joining": date_of_joining,
			"department": random.choice(DEPARTMENTS) if _has_field("Employee", "department") else None,
			"designation": random.choice(DESIGNATIONS) if _has_field("Employee", "designation") else None,
			"status": "Active",
		}

		_set_if_field(emp, "Employee", "custom_department", random.choice(DEPARTMENTS))
		_set_if_field(emp, "Employee", "custom_agreed_salary", random.randint(25000, 150000))
		_set_if_field(emp, "Employee", "custom_vendor", random.choice([None, None, None, "Vendor Co"]))

		if statuses:
			status = statuses[i % len(statuses)] if i < len(statuses) else "Confirmed"
			_set_if_field(emp, "Employee", "custom_confirmation_status", status)
			if status == "Probation" and _has_field("Employee", "custom_probation_end_date"):
				# spread across overdue / due-this-week / comfortably-in-future
				offset = [-5, 3, 45][i % 3]
				emp["custom_probation_end_date"] = add_days(nowdate(), offset)

		try:
			doc = frappe.get_doc({k: v for k, v in emp.items() if v is not None})
			doc.insert(ignore_permissions=True)
			created.append(doc.name)
		except Exception:
			frappe.log_error(title=f"HR Analytics demo data: could not create Employee '{employee_name}'")
			frappe.db.rollback()

	return created


def _create_job_openings(company, count):
	if not frappe.db.exists("DocType", "Job Opening"):
		return
	for i in range(count):
		title = f"{random.choice(DESIGNATIONS)} - Demo {i + 1}"
		if frappe.db.exists("Job Opening", {"job_title": title}):
			continue
		doc = {
			"doctype": "Job Opening",
			"job_title": title,
			"designation": random.choice(DESIGNATIONS),
			"company": company,
			"status": random.choice(["Open", "Open", "Open", "Closed"]),
		}
		try:
			frappe.get_doc(doc).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title=f"HR Analytics demo data: could not create Job Opening '{title}'")
			frappe.db.rollback()


def _create_job_requisitions(company, count):
	if not frappe.db.exists("DocType", "Job Requisition"):
		return
	for i in range(count):
		doc = {
			"doctype": "Job Requisition",
			"designation": random.choice(DESIGNATIONS),
			"company": company,
			"no_of_positions": random.randint(1, 5),
			"status": random.choice(["Open", "Filled", "Open"]),
		}
		_set_if_field(doc, "Job Requisition", "custom_cost_center", random.choice(DEPARTMENTS))
		_set_if_field(doc, "Job Requisition", "custom_role_type", random.choice(["New", "Replacement"]))
		_set_if_field(doc, "Job Requisition", "custom_budgeted", random.choice(["Yes", "No"]))
		_set_if_field(doc, "Job Requisition", "custom_employment_type", random.choice(["Permanent", "Contract"]))
		approved = random.randint(400000, 1500000)
		_set_if_field(doc, "Job Requisition", "custom_approved_budget", approved)
		_set_if_field(doc, "Job Requisition", "custom_consumed_budget", round(approved * random.uniform(0.2, 0.9)))
		try:
			frappe.get_doc({k: v for k, v in doc.items() if v is not None}).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title="HR Analytics demo data: could not create Job Requisition")
			frappe.db.rollback()


def _create_job_applicants(count):
	if not frappe.db.exists("DocType", "Job Applicant"):
		return
	for i in range(count):
		name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
		email = f"demo.applicant.{i}.{random.randint(1000,9999)}@example.com"
		doc = {
			"doctype": "Job Applicant",
			"applicant_name": name,
			"email_id": email,
			"designation": random.choice(DESIGNATIONS),
			"status": random.choice(["Open", "Replied", "Rejected", "Accepted"]),
			"source": random.choice(["Referral", "Job Portal", "Direct", "Walk In"]),
		}
		_set_if_field(doc, "Job Applicant", "custom_department", random.choice(DEPARTMENTS))
		_set_if_field(doc, "Job Applicant", "custom_employment_type", random.choice(["Permanent", "Contract"]))
		_set_if_field(doc, "Job Applicant", "custom_employee_created", random.choice([0, 0, 1]))
		_set_if_field(doc, "Job Applicant", "custom_onboarded", random.choice([0, 1]))
		try:
			frappe.get_doc({k: v for k, v in doc.items() if v is not None}).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title=f"HR Analytics demo data: could not create Job Applicant '{name}'")
			frappe.db.rollback()


def _create_leave_applications(employees):
	if not employees or not frappe.db.exists("DocType", "Leave Application"):
		return
	leave_types = frappe.get_all("Leave Type", filters={"is_lwp": 1}, limit=1, pluck="name") or \
		frappe.get_all("Leave Type", limit=1, pluck="name")
	if not leave_types:
		return
	leave_type = leave_types[0]

	for emp in employees[: min(6, len(employees))]:
		from_date = add_days(nowdate(), random.randint(-10, 20))
		doc = {
			"doctype": "Leave Application",
			"employee": emp,
			"leave_type": leave_type,
			"from_date": from_date,
			"to_date": add_days(from_date, random.randint(0, 3)),
			"status": random.choice(["Open", "Approved"]),
		}
		_set_if_field(doc, "Leave Application", "custom_approval_flow", random.choice(["Single-Layer", "Multi-Layer"]))
		_set_if_field(doc, "Leave Application", "custom_requires_second_approval", random.choice([0, 1]))
		try:
			frappe.get_doc(doc).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title=f"HR Analytics demo data: could not create Leave Application for '{emp}'")
			frappe.db.rollback()
