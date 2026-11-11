from odoo.tests.common import TransactionCase

class TestGiftGuardRuleEngine(TransactionCase):
    def setUp(self):
        super().setUp()
        self.org = self.env["giftguard.organisation"].create({
            "name": "Example Recipient Ltd",
            "policy_owner": "Compliance Team",
        })
        self.policy = self.env["giftguard.policy"].create({
            "name": "Gift Policy v1",
            "organisation_id": self.org.id,
            "source_reference": "Customer-approved test policy",
            "owner_name": "Compliance Team",
            "effective_date": "2026-01-01",
            "review_date": "2027-01-01",
            "state": "verified",
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
        })]

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
