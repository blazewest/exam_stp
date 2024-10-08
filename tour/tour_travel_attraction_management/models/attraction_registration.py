# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class AttractionRegistration(models.Model):
    _inherit = "res.partner"
    _description = "Attraction Registration"

    registration_type = fields.Selection(selection_add=[("attraction", "Attraction")])
    attraction_line_ids = fields.One2many(
        "attraction.service.line", "attraction_id", "Attraction Services"
    )


class AttractionServiceLine(models.Model):
    _name = "attraction.service.line"
    _rec_name = "service_id"
    _description = "Attraction Service Line"

    attraction_id = fields.Many2one("res.partner", "Attraction")
    service_id = fields.Many2one("product.product", "Attraction Service")
    unit_price = fields.Float()
    cost_price = fields.Float()

    @api.onchange("service_id")
    def _onchange_service_id(self):
        if self.service_id:
            self.update(
                {
                    "unit_price": self.service_id.lst_price,
                    "cost_price": self.service_id.standard_price,
                }
            )
