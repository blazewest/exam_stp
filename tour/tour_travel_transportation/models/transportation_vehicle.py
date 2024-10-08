# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class TransportationVehicle(models.Model):
    _name = "transportation.vehicle"
    _description = "Transportation Vehicle "

    product_id = fields.Many2one(
        "product.product",
        "Transportation",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    vehicle_number = fields.Char()
    capacity = fields.Integer()
    currency_id = fields.Many2one('res.currency', 'Currency',
        default=lambda self: self.env.company.currency_id.id)


    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        domain = domain or []
        context = dict(self._context) or {}
        if context.get("journey_date") and context.get("transportation_id"):
            domain = []
            contract = self.env["package.contract"].search(
                [
                    ("transportation_id", "=", context.get("transportation_id")),
                    ("package_contract_type", "=", "transportation"),
                    ("date_start", "<=", context.get("journey_date")),
                    ("date_end", ">=", context.get("journey_date")),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            vehicles = (
                contract.filtered(
                    lambda a: a.transportation_id.id == context.get("transportation_id")
                )
                .mapped("transportation_contract_line_ids")
                .mapped("vehicle_id")
            )
            domain.append(["id", "in", vehicles.ids])
        return super()._search(domain, offset, limit, order, access_rights_uid)



class TransportationVehicleLine(models.Model):
    _name = "transportation.vehicle.line"
    _rec_name = "vehicle_id"
    _description = "Transportation Vehicle Line"

    transportation_id = fields.Many2one("res.partner", "Transportation")
    vehicle_id = fields.Many2one("transportation.vehicle", "Vehicle Type")
    qty = fields.Integer("Quantity")
    cost_price = fields.Float()
    unit_price = fields.Float()
    capacity = fields.Integer()

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.update(
                {
                    "unit_price": self.vehicle_id.list_price,
                    "cost_price": self.vehicle_id.standard_price,
                    "capacity": self.vehicle_id.capacity,
                }
            )
