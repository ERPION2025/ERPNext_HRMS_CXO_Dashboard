import frappe
from frappe.model.document import Document


class DashboardScreen(Document):
	def validate(self):
		self.screen_name = frappe.scrub(self.screen_name or self.title)

	def has_visibility_for(self, user=None):
		"""True if `user` (defaults to session user) can see this screen."""
		user = user or frappe.session.user
		if user == "Administrator":
			return True
		if not self.roles:
			return True
		user_roles = set(frappe.get_roles(user))
		allowed_roles = {r.role for r in self.roles}
		return bool(user_roles & allowed_roles)
