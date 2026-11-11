from odoo import fields, models

class GiftGuardOrganisation(models.Model):
    _name = "giftguard.organisation"
    _description = "Recipient Organisation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    domain = fields.Char(help="Optional verified email domain; not used as proof of identity.")
    policy_owner = fields.Char(required=True, tracking=True)
    policy_email = fields.Char()
    active = fields.Boolean(default=True)
    policy_ids = fields.One2many("giftguard.policy", "organisation_id")
