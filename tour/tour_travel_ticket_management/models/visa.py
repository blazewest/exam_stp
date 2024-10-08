#  See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class VisaPackageLine(models.Model):
    _name = "visa.package.line"
    _description = "Visa"

    name = fields.Text(translate=True)
    product_id = fields.Many2one("product.product", "Visa")
    supplier_id = fields.Many2one("res.partner", "Supplier")
    description = fields.Char()
    visa_status = fields.Char()
    unit_price = fields.Float()
    cost_price = fields.Float()
    sale_order_templete_id = fields.Many2one("sale.order.template", string="Sale Order")
    currency_id = fields.Many2one(
        "res.currency", "Currency", default=lambda self: self.env.company.currency_id
    )
    display_type = fields.Selection(
        [("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
    sequence = fields.Integer()
