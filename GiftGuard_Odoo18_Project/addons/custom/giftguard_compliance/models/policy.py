from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class GiftGuardPolicy(models.Model):
    _name = "giftguard.policy"
    _description = "Organisation Gifting Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, id desc"

    name = fields.Char(string="Policy", required=True, tracking=True)
    organisation_id = fields.Many2one(
        "giftguard.organisation",
        string="Recipient Organisation",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="organisation_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    source_reference = fields.Char(
        required=True,
        help="Document reference or authorised source.",
    )
    owner_name = fields.Char(string="Policy Owner", required=True)
    effective_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    review_date = fields.Date(required=True)
    state = fields.Selection([
        ("draft", "Draft"), ("verified", "Verified"), ("expired", "Expired")
    ], default="draft", required=True, tracking=True)
    rule_ids = fields.One2many("giftguard.rule", "policy_id", string="Rules")
    version = fields.Integer(default=0, readonly=True, copy=False)

    @api.constrains("review_date", "effective_date")
    def _check_dates(self):
        for rec in self:
            if rec.review_date and rec.effective_date and rec.review_date < rec.effective_date:
                raise ValidationError(_("Review date cannot be before effective date."))

    @api.model_create_multi
    def create(self, vals_list):
        if any(
            vals.get("state", "draft") != "draft" or vals.get("version", 0) != 0
            for vals in vals_list
        ):
            raise UserError(_("Policies must be created as a new Draft version."))
        return super().create(vals_list)

    def write(self, vals):
        if "state" in vals or "version" in vals:
            raise UserError(_("Use the policy actions to change its state."))
        if self.filtered(lambda policy: policy.state != "draft"):
            raise UserError(_("Verified or expired policies cannot be changed."))
        return super().write(vals)

    def copy(self, default=None):
        default = dict(default or {})
        default.update({"state": "draft", "version": 0})
        return super().copy(default)

    def action_verify(self):
        for rec in self:
            if not self.env.user.has_group("giftguard_compliance.group_giftguard_manager"):
                raise UserError(_("Only GiftGuard managers can verify policies."))
            if rec.state != "draft":
                raise UserError(_("Only draft policies can be verified."))
            today = fields.Date.context_today(rec)
            if rec.effective_date > today or rec.review_date < today:
                raise UserError(
                    _("A policy can only be verified while it is within its effective dates.")
                )
            if not rec.rule_ids.filtered("active"):
                raise UserError(_("Add at least one active rule before verifying a policy."))
            super(GiftGuardPolicy, rec).write({
                "state": "verified",
                "version": rec.version + 1,
            })

    def action_expire(self):
        for rec in self:
            if not self.env.user.has_group("giftguard_compliance.group_giftguard_manager"):
                raise UserError(_("Only GiftGuard managers can expire policies."))
            if rec.state != "verified":
                raise UserError(_("Only verified policies can be expired."))
            super(GiftGuardPolicy, rec).write({"state": "expired"})

    def unlink(self):
        if self.filtered(lambda policy: policy.state != "draft"):
            raise UserError(_("Verified or expired policies cannot be deleted."))
        return super().unlink()
