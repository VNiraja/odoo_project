from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class GiftGuardPolicy(models.Model):
    _name = "giftguard.policy"
    _description = "Organisation Gifting Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, id desc"

    name = fields.Char(required=True, tracking=True)
    organisation_id = fields.Many2one("giftguard.organisation", required=True, ondelete="restrict", tracking=True)
    source_reference = fields.Char(required=True, help="Document reference or authorised source.")
    owner_name = fields.Char(required=True)
    effective_date = fields.Date(required=True, default=fields.Date.today)
    review_date = fields.Date(required=True)
    state = fields.Selection([
        ("draft", "Draft"), ("verified", "Verified"), ("expired", "Expired")
    ], default="draft", required=True, tracking=True)
    rule_ids = fields.One2many("giftguard.rule", "policy_id")
    version = fields.Integer(default=1, readonly=True)

    @api.constrains("review_date", "effective_date")
    def _check_dates(self):
        for rec in self:
            if rec.review_date and rec.effective_date and rec.review_date < rec.effective_date:
                raise ValidationError(_("Review date cannot be before effective date."))

    def action_verify(self):
        for rec in self:
            rec.write({"state": "verified", "version": rec.version + 1})

    def action_expire(self):
        self.write({"state": "expired"})
