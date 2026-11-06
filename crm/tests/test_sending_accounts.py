# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from crm.api.user import get_sending_accounts


class TestSendingAccountsUnit(UnitTestCase):
	"""get_sending_accounts without a database: frappe.get_all is faked."""

	def run_with(self, user, rows, outgoing):
		calls = []

		def fake_get_all(doctype, filters=None, fields=None, pluck=None, order_by=None):
			calls.append((doctype, filters))
			if doctype == "User Email":
				return [frappe._dict(r) for r in rows]
			if doctype == "Email Account":
				# Apply only the filters the code sends, so dropping one is caught.
				names = filters["name"][1]
				if filters.get("enable_outgoing") == 1:
					names = [name for name in names if name in outgoing]
				return names
			raise AssertionError(doctype)

		with (
			patch.object(frappe, "session", frappe._dict(user=user)),
			patch.object(frappe, "get_all", side_effect=fake_get_all),
		):
			return get_sending_accounts(), calls

	def test_lists_only_outgoing_accounts_in_row_order(self):
		rows = [
			{"email_account": "B", "email_id": "b@x.test"},
			{"email_account": "Off", "email_id": "off@x.test"},
			{"email_account": "A", "email_id": "a@x.test"},
		]
		result, _ = self.run_with("u@x.test", rows, outgoing={"A", "B"})
		self.assertEqual(
			result,
			[
				{"email_account": "B", "email_id": "b@x.test"},
				{"email_account": "A", "email_id": "a@x.test"},
			],
		)

	def test_reads_only_the_session_users_rows(self):
		_, calls = self.run_with("u@x.test", [], outgoing=set())
		doctype, filters = calls[0]
		self.assertEqual(doctype, "User Email")
		self.assertEqual(filters, {"parenttype": "User", "parentfield": "user_emails", "parent": "u@x.test"})

	def test_outgoing_is_checked_on_the_email_account(self):
		rows = [{"email_account": "A", "email_id": "a@x.test", "enable_outgoing": 1}]
		result, _ = self.run_with("u@x.test", rows, outgoing=set())
		self.assertEqual(result, [])

	def test_guest_gets_nothing(self):
		result, calls = self.run_with("Guest", [{"email_account": "A", "email_id": "a@x.test"}], {"A"})
		self.assertEqual(result, [])
		self.assertEqual(calls, [])

	def test_row_without_address_is_skipped(self):
		rows = [{"email_account": "A", "email_id": None}]
		result, _ = self.run_with("u@x.test", rows, outgoing={"A"})
		self.assertEqual(result, [])


class TestSendingAccounts(IntegrationTestCase):
	"""A Sales User without System Manager can't read User.user_emails
	(permlevel 1), but must still get their own From choices."""

	def setUp(self):
		frappe.db.savepoint("test_sending_accounts")
		self.out = make_account("CRM Test Out", "out@sending.test", outgoing=1)
		self.off = make_account("CRM Test Off", "off@sending.test", outgoing=0)
		self.rep = make_user("rep@sending.test", [self.out, self.off])
		self.other = make_user("other@sending.test", [make_account("CRM Test Other", "other@x.test", 1)])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="test_sending_accounts")

	def test_sales_user_gets_own_outgoing_accounts(self):
		frappe.set_user(self.rep)
		self.assertNotIn("System Manager", frappe.get_roles())
		self.assertEqual(
			get_sending_accounts(),
			[{"email_account": self.out, "email_id": "out@sending.test"}],
		)

	def test_user_document_hides_the_table_from_sales_user(self):
		# Why the composer can't read it off the User document.
		frappe.set_user(self.rep)
		doc = frappe.get_doc("User", self.rep)
		doc.apply_fieldlevel_read_permissions()
		self.assertFalse(doc.get("user_emails"))

	def test_never_returns_another_users_accounts(self):
		frappe.set_user(self.rep)
		self.assertNotIn("other@x.test", [a["email_id"] for a in get_sending_accounts()])


def make_account(name, email_id, outgoing):
	if not frappe.db.exists("Email Account", name):
		frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": name,
				"email_id": email_id,
				"enable_incoming": 0,
				"enable_outgoing": outgoing,
				"awaiting_password": 1,
				"smtp_server": "localhost" if outgoing else None,
			}
		).insert(ignore_permissions=True)
	return name


def make_user(email, accounts):
	if not frappe.db.exists("User", email):
		user = frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0]})
		user.append("roles", {"role": "Sales User"})
		for account in accounts:
			user.append("user_emails", {"email_account": account})
		user.insert(ignore_permissions=True)
	return email
