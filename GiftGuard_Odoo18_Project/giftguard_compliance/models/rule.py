from odoo import fields, models

class GiftGuardRule(models.Model):
    _name = "giftguard.rule"
    _description = "Gift Compliance Rule"
    _order = "sequence, id"

    policy_id = fields.Many2one("giftguard.policy", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    rule_type = fields.Selection([
        ("max_value", "Maximum gift value"),
        ("approval_threshold", "Approval threshold"),
        ("prohibited_category", "Prohibited category"),
        ("deal_stage", "Restricted deal stage"),
        ("recipient_limit", "Recipient rolling-period limit"),
    ], required=True)
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one("res.currency")
    amount = fields.Monetary(currency_field="currency_id")
    category = fields.Char(help="Use a controlled category vocabulary agreed with the policy owner.")
    deal_stage = fields.Char()
    max_sends = fields.Integer()
    period_days = fields.Integer(default=30)
    description = fields.Char(required=True)
