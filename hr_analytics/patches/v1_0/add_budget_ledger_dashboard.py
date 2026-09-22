from hr_analytics.install import create_screens, create_widgets


def execute():
	"""Seed the new Budget & Ledger Dashboard Screen/Widgets on sites that
	installed hr_analytics before this screen existed. create_screens() and
	create_widgets() are both idempotent (skip anything already present), so
	this is safe to run alongside the original after_install seed set."""
	create_screens()
	create_widgets()
