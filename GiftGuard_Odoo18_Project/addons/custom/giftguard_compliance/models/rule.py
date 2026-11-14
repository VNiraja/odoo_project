from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class GiftGuardRule(models.Model):
    _name = "giftguard.rule"
    _description = "Gift Compliance Rule"
    _order = "sequence, id"

    policy_id = fields.Many2one(
        "giftguard.policy",
        string="Policy",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="policy_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    sequence = fields.Integer(default=10, index=True)
    rule_type = fields.Selection([
        ("max_value", "Maximum gift value"),
        ("approval_threshold", "Approval threshold"),
        ("prohibited_category", "Prohibited category"),
        ("deal_stage", "Restricted deal stage"),
        ("recipient_limit", "Recipient rolling-period approved-request limit"),
    ], required=True)
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        help="Required for maximum-value and approval-threshold rules.",
    )
    amount = fields.Monetary(
        currency_field="currency_id",
        help="Compared only when the request uses this same currency.",
    )
    category = fields.Char(
        help="Use a controlled category vocabulary agreed with the policy owner."
    )
    deal_stage = fields.Char(string="Restricted Deal Stage")
    max_sends = fields.Integer(
        string="Maximum Approved Requests",
        help="Counts previously approved requests, not gifts confirmed as delivered.",
    )
    period_days = fields.Integer(
        string="Rolling Period (Days)",
        default=30,
    )
    description = fields.Char(required=True)

    @api.constrains(
        "rule_type",
        "currency_id",
        "amount",
        "category",
        "deal_stage",
        "max_sends",
        "period_days",
    )
    def _check_rule_configuration(self):
        for rule in self:
            if rule.rule_type in ("max_value", "approval_threshold"):
                if not rule.currency_id:
                    raise ValidationError(
                        _("Amount rules require a currency.")
                    )
                if rule.amount < 0:
                    raise ValidationError(_("Rule amounts cannot be negative."))
            elif rule.rule_type == "prohibited_category" and (
                not rule.category or not rule.category.strip()
            ):
                raise ValidationError(
                    _("A prohibited-category rule requires a category.")
                )
            elif rule.rule_type == "deal_stage" and (
                not rule.deal_stage or not rule.deal_stage.strip()
            ):
                raise ValidationError(
                    _("A deal-stage rule requires a deal stage.")
                )
            elif rule.rule_type == "recipient_limit":
                if rule.max_sends <= 0 or rule.period_days <= 0:
                    raise ValidationError(
                        _("Recipient limits require positive request and period limits.")
                    )

    @api.model_create_multi
    def create(self, vals_list):
        policy_ids = [vals.get("policy_id") for vals in vals_list if vals.get("policy_id")]
        policies = self.env["giftguard.policy"].browse(policy_ids)
        if policies.filtered(lambda policy: policy.state != "draft"):
            raise ValidationError(_("Rules can only be added to draft policies."))
        return super().create(vals_list)

    def write(self, vals):
        policy = self.mapped("policy_id")
        if "policy_id" in vals:
            policy |= self.env["giftguard.policy"].browse(vals["policy_id"])
        if policy.filtered(lambda item: item.state != "draft"):
            raise ValidationError(_("Rules on verified or expired policies cannot be changed."))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda rule: rule.policy_id.state != "draft"):
            raise ValidationError(_("Rules on verified or expired policies cannot be deleted."))
        return super().unlink()
