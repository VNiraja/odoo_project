from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGiftGuardRuleEngine(TransactionCase):
    def setUp(self):
        super().setUp()
        self.org = self.env["giftguard.organisation"].create({
            "name": "Example Recipient Ltd",
            "policy_owner": "Compliance Team",
        })
        today = fields.Date.context_today(self)
        self.policy = self.env["giftguard.policy"].create({
            "name": "Gift Policy v1",
            "organisation_id": self.org.id,
            "source_reference": "Customer-approved test policy",
            "owner_name": "Compliance Team",
            "effective_date": fields.Date.to_string(today - timedelta(days=1)),
            "review_date": fields.Date.to_string(today + timedelta(days=365)),
        })
        self.policy.rule_ids = [(0, 0, {
            "rule_type": "max_value",
            "currency_id": self.env.company.currency_id.id,
            "amount": 3000,
            "description": "Maximum gift value",
        }), (0, 0, {
            "rule_type": "prohibited_category",
            "category": "alcohol",
            "description": "Alcohol is prohibited",
        }), (0, 0, {
            "rule_type": "recipient_limit",
            "max_sends": 2,
            "period_days": 30,
            "description": "Maximum two approved requests in 30 days",
        })]
        self.policy.action_verify()

    def _request(self, amount=1000, category="books"):
        return self.env["giftguard.request"].create({
            "organisation_id": self.org.id,
            "recipient_ref": "recipient-hash-001",
            "gift_description": "Demo gift",
            "category": category,
            "amount": amount,
            "currency_id": self.env.company.currency_id.id,
        })

    def test_approved_under_cap(self):
        req = self._request()
        req.action_evaluate()
        self.assertEqual(req.status, "approved")

    def test_blocked_over_cap(self):
        req = self._request(amount=3500)
        req.action_evaluate()
        self.assertEqual(req.status, "blocked")

    def test_blocked_prohibited_category(self):
        req = self._request(category="Alcohol")
        req.action_evaluate()
        self.assertEqual(req.status, "blocked")

    def test_currency_mismatch_requires_review(self):
        currency = self.env["res.currency"].search(
            [("id", "!=", self.env.company.currency_id.id)],
            limit=1,
        )
        if not currency:
            self.skipTest("No second currency is configured.")
        req = self._request()
        req.currency_id = currency
        req.action_evaluate()
        self.assertEqual(req.status, "review_required")

    def test_recipient_limit_counts_only_approved_requests(self):
        for _index in range(2):
            req = self._request()
            req.action_evaluate()
            self.assertEqual(req.status, "approved")

        req = self._request()
        req.action_evaluate()
        self.assertEqual(req.status, "blocked")
        self.assertIn("approved-request limit", req.decision_reason)

    def test_verified_policy_and_rules_are_immutable(self):
        with self.assertRaises(UserError):
            self.policy.write({"name": "Changed policy"})
        with self.assertRaises(ValidationError):
            self.policy.rule_ids[0].write({"amount": 5000})

    def test_policy_requires_active_rule_to_verify(self):
        policy = self.env["giftguard.policy"].create({
            "name": "Empty Policy",
            "organisation_id": self.org.id,
            "source_reference": "Customer-approved test policy",
            "owner_name": "Compliance Team",
            "effective_date": fields.Date.context_today(self),
            "review_date": fields.Date.context_today(self) + timedelta(days=30),
        })
        with self.assertRaises(UserError):
            policy.action_verify()

    def test_missing_deal_stage_requires_review_when_restricted(self):
        organisation = self.env["giftguard.organisation"].create({
            "name": "Stage Restricted Recipient",
            "policy_owner": "Compliance Team",
        })
        today = fields.Date.context_today(self)
        policy = self.env["giftguard.policy"].create({
            "name": "Restricted Stage Policy",
            "organisation_id": organisation.id,
            "source_reference": "Customer-approved test policy",
            "owner_name": "Compliance Team",
            "effective_date": today,
            "review_date": today + timedelta(days=30),
        })
        policy.rule_ids = [(0, 0, {
            "rule_type": "deal_stage",
            "deal_stage": "negotiation",
            "description": "Review requests during negotiation",
        })]
        policy.action_verify()
        req = self.env["giftguard.request"].create({
            "organisation_id": organisation.id,
            "recipient_ref": "recipient-hash-stage",
            "gift_description": "Demo gift",
            "category": "books",
            "amount": 100,
            "currency_id": self.env.company.currency_id.id,
        })
        req.action_evaluate()
        self.assertEqual(req.status, "review_required")
        self.assertIn("Deal stage is missing", req.decision_reason)

    def test_evaluated_request_cannot_be_changed_or_manually_approved(self):
        req = self._request()
        req.action_evaluate()
        duplicate = req.copy()
        self.assertEqual(duplicate.status, "draft")
        self.assertFalse(duplicate.policy_id)
        with self.assertRaises(UserError):
            req.write({"status": "approved"})
        with self.assertRaises(UserError):
            req.write({"amount": 1})

    def test_request_cannot_be_created_with_a_forged_decision(self):
        with self.assertRaises(UserError):
            self.env["giftguard.request"].create({
                "organisation_id": self.org.id,
                "recipient_ref": "recipient-hash-002",
                "gift_description": "Demo gift",
                "category": "books",
                "amount": 100,
                "currency_id": self.env.company.currency_id.id,
                "status": "approved",
            })

    def test_review_approval_requires_a_reason(self):
        currency = self.env["res.currency"].search(
            [("id", "!=", self.env.company.currency_id.id)],
            limit=1,
        )
        if not currency:
            self.skipTest("No second currency is configured.")
        req = self._request()
        req.currency_id = currency
        req.action_evaluate()
        self.assertEqual(req.status, "review_required")
        with self.assertRaises(UserError):
            req.action_approve_review()
        req.reviewer_note = "Confirmed with the policy owner."
        req.action_approve_review()
        self.assertEqual(req.status, "approved")

    def test_negative_amount_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._request(amount=-1)

    def test_company_record_rule_hides_other_company_data(self):
        company_b = self.env["res.company"].create({"name": "Company B"})
        organisation_b = self.env["giftguard.organisation"].create({
            "name": "Company B Recipient",
            "policy_owner": "Compliance Team",
            "company_id": company_b.id,
        })
        user = self.env["res.users"].create({
            "name": "GiftGuard User",
            "login": "giftguard_company_rule_user",
            "groups_id": [(6, 0, [self.env.ref(
                "giftguard_compliance.group_giftguard_user"
            ).id])],
            "company_id": self.env.company.id,
            "company_ids": [(6, 0, [self.env.company.id])],
        })
        with self.assertRaises(AccessError):
            organisation_b.with_user(user).read(["name"])
