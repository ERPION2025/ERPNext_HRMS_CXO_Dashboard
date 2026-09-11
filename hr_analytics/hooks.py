from . import __version__ as app_version

app_name = "hr_analytics"
app_title = "HR Analytics"
app_publisher = "ERPion Technologies LLP"
app_description = "Native ERPNext/HRMS dashboards for Recruitment, Onboarding, Probation, Leave, Appraisal and Executive reporting — with a UI to add or hide charts, and workflow-stage visuals."
app_email = "hello@erpion.in"
app_license = "MIT"
required_apps = ["frappe", "erpnext", "hrms"]

# Assets
# ------
app_include_js = "/assets/hr_analytics/js/dashboard_core.js"
app_include_css = "/assets/hr_analytics/css/hr_analytics.css"

# Installation
# ------------
after_install = "hr_analytics.install.after_install"

# Fixtures — exported if you bench --site <site> export-fixtures after editing
# widgets/screens by hand; the seed set itself is created in install.py so a
# fresh install always ships with the full pre-built widget library.
fixtures = [
	{"dt": "Dashboard Screen"},
	{"dt": "Dashboard Widget"},
]

# Website / desk
# ---------------
# The dashboard is also reachable at /app/hr-dashboard as a normal Desk Page
# (see hr_analytics/page/hr_dashboard). No portal/website route is exposed —
# keeps everything behind normal Frappe desk login + role permissions.
