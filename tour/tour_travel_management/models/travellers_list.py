#  See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class TravellersList(models.Model):
    _name = "travellers.list"
    _description = "Travellers List"

    # Client did not required birthday field
    # @api.depends("birth_date")
    # def _compute_traveler_age(self):
    #     for rec in self:
    #         rec.age=0
    #         if rec.birth_date:
    #             rec.age= relativedelta(fields.Date.context_today(self), rec.birth_date).years

    #    partner_id = fields.Many2one('res.partner','Name', required=True)
    name = fields.Char(required=True)
    #  Client did not required birthday field
    # birth_date = fields.Date("Date of Birth", required=True)
    age = fields.Integer()
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")]
    )
    remarks = fields.Char()
    identity_type = fields.Selection(
        [
            ("voter_id", "Voter ID"),
            ("driving license", "Driving License"),
            ("passport", "Passport Number"),
            ("other", "Other Proof"),
        ],
        string="ID Type",
    )
    identity_number = fields.Char("Identity Proof number")
    identities_images = fields.Many2many(
        "ir.attachment", string="Identity Proof", help="Multi Image upload"
    )
    color = fields.Integer(string="Color Index", default=0)
    package_id = fields.Many2one(
        "sale.order.template", "Package", domain=[("is_package", "=", True)]
    )
    sale_order_id = fields.Many2one("sale.order", "Order")
    invoice_id = fields.Many2one("account.move", "Invoice")
