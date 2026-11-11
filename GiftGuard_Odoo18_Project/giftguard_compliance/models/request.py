from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class GiftGuardRequest(models.Model):
    _name = "giftguard.request"
    _description = "Gift Compliance Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(default=lambda self: _("New"), readonly=True, copy=False)
    organisation_id = fields.Many2one("giftguard.organisation", required=True, ondelete="restrict")
    policy_id = fields.Many2one("giftguard.policy", readonly=True, ondelete="restrict")
    recipient_ref = fields.Char(required=True, help="Use a pseudonymous or customer-side reference where possible.")
    recipient_email = fields.Char(help="Only retain if needed for the agreed workflow.")
    gift_description = fields.Char(required=True)
    category = fields.Char(required=True)
    amount = fields.Monetary(required=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)
    deal_stage = fields.Char()
    status = fields.Selection([
        ("draft", "Draft"), ("approved", "Approved"),
        ("blocked", "Blocked"), ("review_required", "Review Required"),
        ("rejected", "Rejected"),
    ], default="draft", tracking=True, readonly=True)
    decision_reason = fields.Text(readonly=True)
    policy_version = fields.Integer(readonly=True)
    evaluated_at = fields.Datetime(readonly=True)
    reviewer_id = fields.Many2one("res.users", readonly=True)
    reviewer_note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("giftguard.request") or _("New")
        return super().create(vals_list)

    def action_evaluate(self):
        for rec in self:
            result = rec._evaluate()
            rec.write({
                "policy_id": result.get("policy_id"),
                "status": result["status"],
                "decision_reason": result["reason"],
                "policy_version": result.get("version", 0),
                "evaluated_at": fields.Datetime.now(),
            })
        return True

    def _evaluate(self):
        self.ensure_one()
        today = date.today()
        policy = self.env["giftguard.policy"].search([
            ("organisation_id", "=", self.organisation_id.id),
            ("state", "=", "verified"),
            ("effective_date", "<=", today),
            ("review_date", ">=", today),
        ], order="effective_date desc, id desc", limit=1)

        if not policy:
            return {"status": "review_required", "reason": "No current verified policy is available; compliance owner review required."}

        reasons = []
        review = []
        for rule in policy.rule_ids.filtered("active").sorted("sequence"):
            if rule.rule_type == "max_value":
                if not rule.currency_id or rule.currency_id == self.currency_id:
                    if self.amount > rule.amount:
                        reasons.append(f"Gift value {self.amount:.2f} exceeds maximum {rule.amount:.2f}.")
                else:
                    review.append("Currency conversion is not configured; value rule requires manual review.")
            elif rule.rule_type == "approval_threshold":
                if rule.currency_id and rule.currency_id != self.currency_id:
                    review.append("Currency conversion is not configured for approval threshold.")
                elif self.amount > rule.amount:
                    review.append(f"Gift exceeds approval threshold {rule.amount:.2f}; reviewer approval required.")
            elif rule.rule_type == "prohibited_category":
                if (rule.category or "").strip().casefold() == (self.category or "").strip().casefold():
                    reasons.append(f"Gift category '{self.category}' is prohibited.")
            elif rule.rule_type == "deal_stage":
                if rule.deal_stage and (self.deal_stage or "").strip().casefold() == rule.deal_stage.strip().casefold():
                    review.append(f"Deal stage '{self.deal_stage}' requires compliance review.")
            elif rule.rule_type == "recipient_limit":
                # Conservative MVP: count historical approved/reviewed requests for this policy+recipient.
                # Production version must use a defined rolling-window timezone and concurrency-safe aggregation.
                from datetime import timedelta
                since = fields.Datetime.now() - timedelta(days=rule.period_days or 30)
                count = self.search_count([
                    ("id", "!=", self.id),
                    ("organisation_id", "=", self.organisation_id.id),
                    ("recipient_ref", "=", self.recipient_ref),
                    ("evaluated_at", ">=", since),
                    ("status", "in", ["approved", "review_required"]),
                ])
                if rule.max_sends and count >= rule.max_sends:
                    reasons.append(f"Recipient send limit reached: {rule.max_sends} in {rule.period_days} days.")

        if reasons:
            status, reason = "blocked", " ".join(reasons)
        elif review:
            status, reason = "review_required", " ".join(review)
        else:
            status, reason = "approved", "All configured rules passed."
        return {"status": status, "reason": reason, "policy_id": policy.id, "version": policy.version}

    def action_approve_review(self):
        for rec in self:
            if not self.env.user.has_group("giftguard_compliance.group_giftguard_reviewer"):
                raise UserError(_("Only compliance reviewers can approve requests."))
            if rec.status != "review_required":
                raise UserError(_("Only review-required requests can be approved."))
            rec.write({"status": "approved", "reviewer_id": self.env.user.id})
            rec.message_post(body=_("Approved by %s. %s") % (self.env.user.name, rec.reviewer_note or ""))

    def action_reject_review(self):
        for rec in self:
            if not self.env.user.has_group("giftguard_compliance.group_giftguard_reviewer"):
                raise UserError(_("Only compliance reviewers can reject requests."))
            if rec.status != "review_required":
                raise UserError(_("Only review-required requests can be rejected."))
            rec.write({"status": "rejected", "reviewer_id": self.env.user.id})
            rec.message_post(body=_("Rejected by %s. %s") % (self.env.user.name, rec.reviewer_note or ""))
