from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class GiftGuardRequest(models.Model):
    _name = "giftguard.request"
    _description = "Gift Compliance Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        default=lambda self: _("New"),
        readonly=True,
        copy=False,
        index=True,
    )
    organisation_id = fields.Many2one(
        "giftguard.organisation",
        string="Recipient Organisation",
        required=True,
        ondelete="restrict",
        index=True,
    )
    company_id = fields.Many2one(
        related="organisation_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    policy_id = fields.Many2one(
        "giftguard.policy",
        readonly=True,
        ondelete="restrict",
        index=True,
        copy=False,
    )
    recipient_ref = fields.Char(
        required=True,
        index=True,
        help="Use a pseudonymous or customer-side reference where possible.",
    )
    recipient_email = fields.Char(
        help="Only retain if needed for the agreed workflow."
    )
    gift_description = fields.Char(required=True)
    category = fields.Char(required=True, index=True)
    amount = fields.Monetary(
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    deal_stage = fields.Char()
    status = fields.Selection([
        ("draft", "Draft"), ("approved", "Approved"),
        ("blocked", "Blocked"), ("review_required", "Review Required"),
        ("rejected", "Rejected"),
    ], default="draft", tracking=True, readonly=True, copy=False)
    decision_reason = fields.Text(readonly=True, tracking=True, copy=False)
    policy_version = fields.Integer(readonly=True, copy=False)
    evaluated_at = fields.Datetime(readonly=True, tracking=True, copy=False)
    reviewer_id = fields.Many2one("res.users", readonly=True, tracking=True, copy=False)
    reviewer_note = fields.Text(copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        decision_fields = {
            "status",
            "policy_id",
            "decision_reason",
            "policy_version",
            "evaluated_at",
            "reviewer_id",
            "reviewer_note",
        }
        for vals in vals_list:
            if decision_fields.intersection(vals) or vals.get("status", "draft") != "draft":
                raise UserError(_("Requests must be created in Draft state."))
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("giftguard.request") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        protected_fields = {
            "status",
            "policy_id",
            "decision_reason",
            "policy_version",
            "evaluated_at",
            "reviewer_id",
        }
        if protected_fields.intersection(vals):
            raise UserError(_("Use the request actions to record a compliance decision."))
        if "reviewer_note" in vals:
            if not self.env.user.has_group("giftguard_compliance.group_giftguard_reviewer"):
                raise UserError(_("Only compliance reviewers can update reviewer notes."))
            if self.filtered(lambda record: record.status != "review_required"):
                raise UserError(_("Reviewer notes can only be changed on requests under review."))
        input_fields = {
            "organisation_id",
            "recipient_ref",
            "recipient_email",
            "gift_description",
            "category",
            "amount",
            "currency_id",
            "deal_stage",
        }
        if input_fields.intersection(vals) and self.filtered(
            lambda record: record.status != "draft"
        ):
            raise UserError(_("An evaluated request cannot be changed."))
        return super().write(vals)

    @api.constrains("amount")
    def _check_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError(_("Gift amount cannot be negative."))

    @api.constrains("recipient_ref", "gift_description", "category")
    def _check_required_text(self):
        for rec in self:
            if any(
                not value or not value.strip()
                for value in (rec.recipient_ref, rec.gift_description, rec.category)
            ):
                raise ValidationError(
                    _("Recipient reference, gift description, and category cannot be empty.")
                )

    def action_evaluate(self):
        for rec in self:
            if rec.status != "draft":
                raise UserError(_("Only draft requests can be evaluated."))
            result = rec._evaluate()
            super(GiftGuardRequest, rec).write({
                "policy_id": result.get("policy_id"),
                "status": result["status"],
                "decision_reason": result["reason"],
                "policy_version": result.get("version", 0),
                "evaluated_at": fields.Datetime.now(),
            })
            rec.message_post(
                body=_("Compliance decision: %(status)s. %(reason)s")
                % {"status": result["status"], "reason": result["reason"]}
            )
        return True

    def _evaluate(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        if not self.organisation_id.active:
            return {
                "status": "review_required",
                "reason": "Recipient organisation is inactive; compliance owner review required.",
            }
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
        for rule in policy.rule_ids.filtered("active").sorted(
            key=lambda item: (item.sequence, item.id)
        ):
            if rule.rule_type == "max_value":
                if rule.currency_id != self.currency_id:
                    review.append("Currency conversion is not configured; value rule requires manual review.")
                elif self.currency_id.compare_amounts(self.amount, rule.amount) > 0:
                    reasons.append(
                        f"Gift value {self.amount:.2f} exceeds maximum {rule.amount:.2f} "
                        f"{rule.currency_id.name}."
                    )
            elif rule.rule_type == "approval_threshold":
                if rule.currency_id != self.currency_id:
                    review.append("Currency conversion is not configured for approval threshold.")
                elif self.currency_id.compare_amounts(self.amount, rule.amount) > 0:
                    review.append(
                        f"Gift exceeds approval threshold {rule.amount:.2f} "
                        f"{rule.currency_id.name}; reviewer approval required."
                    )
            elif rule.rule_type == "prohibited_category":
                if rule.category.strip().casefold() == self.category.strip().casefold():
                    reasons.append(f"Gift category '{self.category}' is prohibited.")
            elif rule.rule_type == "deal_stage":
                if not self.deal_stage:
                    review.append("Deal stage is missing; the restricted-stage rule requires manual review.")
                elif self.deal_stage.strip().casefold() == rule.deal_stage.strip().casefold():
                    review.append(f"Deal stage '{self.deal_stage}' requires compliance review.")
            elif rule.rule_type == "recipient_limit":
                since = fields.Datetime.now() - timedelta(days=rule.period_days)
                count = self.search_count([
                    ("id", "!=", self.id),
                    ("organisation_id", "=", self.organisation_id.id),
                    ("recipient_ref", "=", self.recipient_ref),
                    ("create_date", ">=", since),
                    ("status", "=", "approved"),
                ])
                if count >= rule.max_sends:
                    reasons.append(
                        f"Recipient approved-request limit reached: "
                        f"{rule.max_sends} in {rule.period_days} days."
                    )

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
            if not rec.reviewer_note or not rec.reviewer_note.strip():
                raise UserError(_("Enter a reviewer note before approving this request."))
            super(GiftGuardRequest, rec).write({
                "status": "approved",
                "reviewer_id": self.env.user.id,
            })
            rec.message_post(body=_("Approved by %s. %s") % (self.env.user.name, rec.reviewer_note or ""))

    def action_reject_review(self):
        for rec in self:
            if not self.env.user.has_group("giftguard_compliance.group_giftguard_reviewer"):
                raise UserError(_("Only compliance reviewers can reject requests."))
            if rec.status != "review_required":
                raise UserError(_("Only review-required requests can be rejected."))
            if not rec.reviewer_note or not rec.reviewer_note.strip():
                raise UserError(_("Enter a reviewer note before rejecting this request."))
            super(GiftGuardRequest, rec).write({
                "status": "rejected",
                "reviewer_id": self.env.user.id,
            })
            rec.message_post(body=_("Rejected by %s. %s") % (self.env.user.name, rec.reviewer_note or ""))
