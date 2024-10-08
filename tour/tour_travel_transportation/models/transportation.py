# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class TransportationRegistration(models.Model):
    _inherit = "res.partner"
    _description = "Transportation Registration"

    @api.depends("transportation_contract_ids")
    def _compute_transportation_contract_count(self):
        contract_obj = self.env["package.contract"]
        for transport in self:
            transport.transportation_contract_count = contract_obj.search_count(
                [
                    ("transportation_id", "=", transport.id),
                    ("package_contract_type", "=", "transportation"),
                ]
            )

    def _compute_running_contract(self):
        contract_obj = self.env["package.contract"]
        res = super(TransportationRegistration, self)._compute_running_contract()
        for transport in self:
            running_contract = contract_obj.search_count(
                [("transportation_id", "=", transport.id), ("state", "=", "open")]
            )
            if running_contract != 0:
                transport.update({"is_contract_running": True})
        return res

    vehicle_line_ids = fields.One2many(
        "transportation.vehicle.line", "transportation_id", "Vehicles"
    )
    registration_type = fields.Selection(
        selection_add=[("transportation", "Transportation")]
    )
    transportation_contract_count = fields.Integer(
        "Transportation Contract", compute="_compute_transportation_contract_count"
    )
    transportation_contract_ids = fields.One2many(
        "package.contract", "transportation_id", "Transportation Contracts"
    )


    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        domain = domain or []
        context = dict(self._context) or {}
        if (
            context.get("city_id")
            and context.get("package_contract_type") == "transportation"
        ):
            domain = [
                ("city_id", "=", context.get("city_id")),
                ("registration_type", "=", "transportation"),
            ]
        return super()._search(domain, offset, limit, order, access_rights_uid)

