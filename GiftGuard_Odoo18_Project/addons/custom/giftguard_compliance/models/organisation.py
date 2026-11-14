from odoo import fields, models, _
from odoo.exceptions import UserError


class GiftGuardOrganisation(models.Model):
    _name = "giftguard.organisation"
    _description = "Recipient Organisation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(
        string="Organisation",
        required=True,
        tracking=True,
        index=True,
    )
    domain = fields.Char(
        string="Email Domain",
        help="Optional verified email domain; not used as proof of identity.",
    )
    policy_owner = fields.Char(
        string="Policy Owner",
        required=True,
        tracking=True,
    )
    policy_email = fields.Char(string="Policy Contact Email")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    active = fields.Boolean(default=True)
    policy_ids = fields.One2many(
        "giftguard.policy",
        "organisation_id",
        string="Policies",
    )
    request_ids = fields.One2many(
        "giftguard.request",
        "organisation_id",
        string="Gift Requests",
    )

    def write(self, vals):
        if "company_id" in vals and self.filtered(
            lambda organisation: organisation.company_id.id != vals["company_id"]
            and (organisation.policy_ids or organisation.request_ids)
        ):
            raise UserError(
                _("An organisation with policies or requests cannot be moved to another company.")
            )
        return super().write(vals)
