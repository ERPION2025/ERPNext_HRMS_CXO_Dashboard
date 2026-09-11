# HR Analytics

Native ERPNext/HRMS dashboards for Recruitment, Onboarding, Probation & Confirmation,
Leave, and Appraisal, plus an Executive roll-up — built as a normal Frappe app so the
data never leaves your site and every screen sits behind your existing Desk permissions.
Exit/offboarding is intentionally not included in this version.

## What's in here

- **Dashboard Screen** / **Dashboard Widget** doctypes — the config engine. Every
  chart, scorecard and table on every screen is a `Dashboard Widget` record: doctype,
  filters, group-by field, aggregate, chart type, and an `is_active` flag. Untick
  `is_active` to hide a widget without deleting it — same for whole screens via
  `Dashboard Screen`. Both are Frappe doctypes, so creating a new widget is just
  filling in a form, no deploy required.
- **`hr_analytics/api/widgets.py`** — the generic engine that reads a `Dashboard
  Widget` record and returns its data, either via the generic group-by/aggregate
  builder or by calling a custom whitelisted method (`api_override`) for aggregations
  the generic builder can't express (budget-chain joins, leave liability, etc).
- **`hr_analytics/api/workflow.py`** — introspects the real `Workflow` doctype and
  its `Workflow Document State` children for whatever doctype you point it at, so the
  approval-stage timelines always show your actual states, never guessed ones. Used
  for Job Requisition, Job Applicant (`custom_recruitment_status`), Leave
  Application, Mid-Year Review, and Annual Performance Review.
- **`hr_analytics/api/{recruitment,onboarding,probation,leave,appraisal,executive}.py`**
  — the module-specific aggregations built against your custom fields.
- **`hr_analytics/install.py`** — seeds six screens and ~35 pre-built widgets on
  install (`after_install` hook), so you land with a full dashboard and hide what you
  don't want rather than building from zero.
- **`hr_analytics/page/hr_dashboard`** + **`public/js/dashboard_core.js`** — the
  Desk page at `/app/hr-dashboard`: sidebar per screen, a company/date-range filter
  bar, and dependency-free bar/donut/timeline/table renderers (no external chart
  library — everything is plain CSS/SVG, so nothing calls out to the internet).

## Install

```bash
cd ~/frappe-bench
bench get-app hr_analytics /path/to/hr_analytics   # or your git remote once you push it
bench --site <your-site> install-app hr_analytics
```

Reinstalling widgets after editing `install.py` (e.g. you fixed a fieldname):

```bash
bench --site <your-site> execute hr_analytics.install.create_widgets
```

It's idempotent — existing widgets with the same name are left alone.

## Required custom fields — add these before installing

This app was built against a specific ERPNext/HRMS site's customizations. **The
Custom Field definitions themselves are not part of this app** — only the code
that reads them. On a site that doesn't already have them, `install.py` will
still run, but it skips (and logs an error for) any widget whose
`group_by_field`/`filters` reference a field that doesn't exist yet — so most
of Recruitment, Probation and Leave would come up empty until these are added
via Customize Form (or your own Custom Field fixtures):

| DocType | Field | Expected type | Used for |
|---|---|---|---|
| Employee | `custom_confirmation_status` | Select (`Probation`/`Confirmed`/`Extended`) | Probation & Executive screens |
| Employee | `custom_probation_end_date` | Date | Probation due/overdue widgets |
| Employee | `custom_department` | Data or Link | Applicants/probation grouping |
| Employee | `custom_agreed_salary` | Currency | Leave liability estimate |
| Employee | `custom_vendor` | Data or Link, nullable | Direct vs vendor sourcing mix |
| Job Requisition | `custom_approved_budget`, `custom_consumed_budget`, `custom_remaining_budget` | **Currency or Float** (see caveat below) | Budget utilization widgets |
| Job Requisition | `custom_cost_center` | Link or Data | Budget-by-cost-center grouping |
| Job Requisition | `custom_budgeted` | Select (`Yes`/`No`) | Budgeted vs non-budgeted donut |
| Job Requisition | `custom_role_type` | Select | Requisitions-by-role-type bar |
| Job Applicant | `custom_recruitment_status` | Select, driven by a `Workflow` on Job Applicant | Candidate stage timeline |
| Job Applicant | `custom_department` | Data or Link | Applicants-by-department bar |
| Job Applicant | `custom_employment_type` | Select | Applicants-by-employment-type bar |
| Job Applicant | `custom_employee_created` | Check | Handoff funnel |
| Job Applicant | `custom_onboarded` | Check | Handoff funnel |
| Leave Application | `custom_approval_flow` | Select (`Single-Layer`/`Multi-Layer`) | Pending-by-flow donut |
| Leave Application | `custom_requires_second_approval` | Check | Awaiting-second-approval card |

If you're installing on a site where these already exist (e.g. your production
ERPNext/HRMS instance), nothing to do — this table is just documentation.

## Before you rely on these numbers — three things in your schema to fix first

1. **`Job Requisition.custom_approved_budget` / `custom_consumed_budget` /
   `custom_remaining_budget` are typed Data, not Currency.** The budget-utilization
   widgets `sum()` them — that only works reliably on a numeric field type. Switch
   them to Currency (or Float) via Customize Form.
2. **No `custom_confirmation_date` field on Employee.** "Confirmed this month"
   currently falls back to the record's `modified` timestamp, which over-counts any
   Employee edited for unrelated reasons. Add a real confirmation-date field, set it
   from the Probation Review workflow's Confirmed transition, and swap it into
   `api/probation.py::get_confirmed_this_month_count`.
3. **`Mid-Year Review` / `Annual Performance Review` employee-link fieldnames are
   unconfirmed.** Your fields export only showed their `workflow_state`
   customization, not their full schema, so `DOCTYPE_EMPLOYEE_FIELD` in
   `api/appraisal.py` is a placeholder. The two "completion by department" widgets
   ship with `is_active = 0` for that reason — confirm the fieldname, update the map,
   then switch them on.

## Adding a chart from the UI

Desk → HR Analytics → Dashboard Widget → New. Pick the screen, doctype, group-by
field and chart type; save. It's live on that screen immediately — no restart, no
deploy. This is the same mechanism the seeded widgets use.

## Testing locally before deploying

You need a Frappe bench with `frappe`, `erpnext` and `hrms` already installed on
a site (this app declares them as `required_apps` in hooks.py, so
`install-app` will refuse to run without them). The quickest way to get that
on Windows is Docker, via the official
[frappe_docker](https://github.com/frappe/frappe_docker) `pwd.yml` (production-like,
easiest) or dev-container setup:

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
docker compose -f pwd.yml up -d
# wait for the site-creation job to finish, then create a site with erpnext+hrms:
docker compose -f pwd.yml exec backend bench new-site test.local \
  --install-app erpnext --install-app hrms \
  --admin-password admin --mariadb-root-password admin
```

Then get this app into the bench (copy or mount this repo folder into the
container, or push it to a git remote first and `bench get-app <url>`):

```bash
docker compose -f pwd.yml exec backend bench get-app hr_analytics /path/to/hr_analytics
docker compose -f pwd.yml exec backend bench --site test.local install-app hr_analytics
```

Seed sample data so the dashboard has something to show
(`hr_analytics/demo_data.py` — creates Employees, Job Openings, Job
Requisitions, Job Applicants and Leave Applications; it checks each
`custom_*` field against the site's real schema before writing to it, so it
degrades gracefully instead of failing outright if some fields listed above
aren't present):

```bash
docker compose -f pwd.yml exec backend bench --site test.local execute hr_analytics.demo_data.create_demo_data
```

Log into `http://test.local` (or `http://localhost:8080` depending on your
compose setup) as Administrator and open **HR Dashboard** from the Desk
sidebar, or go directly to `/app/hr-dashboard`. Click through all six
screens, toggle the Company/date filters, and check the browser console for
errors — that exercises both the generic widget engine and every
`api_override`.

## Deploying to Frappe Cloud

Frappe Cloud installs custom apps from a git repository, not a zip. This repo
is already laid out correctly (`pyproject.toml` + `hr_analytics/` at the repo
root, which is what `bench get-app` expects):

1. Push this repo to GitHub/GitLab (public, or private with Frappe Cloud
   given access).
2. In the Frappe Cloud dashboard: **Bench → Apps → Install App**, paste the
   repo URL and pick the branch.
3. Add the app to your site the same way as any other custom app, then
   confirm the [required custom fields](#required-custom-fields--add-these-before-installing)
   already exist on that site (Frappe Cloud production sites won't have them
   unless you add them there too, via Customize Form or your own fixtures
   export).

The `dist/` folder in this repo holds the original uploaded zip for
reference — it isn't part of the installable app and bench ignores it.
