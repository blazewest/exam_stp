# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class HotelRegistration(models.Model):
    _inherit = "res.partner"
    _description = "Hotel Registration"

    @api.depends("hotel_contract_ids")
    def _compute_hotel_contract_count(self):
        contract_obj = self.env["package.contract"]
        for hotel in self:
            hotel.hotel_contract_count = contract_obj.search_count(
                [("package_contract_type", "=", "hotel"), ("hotel_id", "=", hotel.id)]
            )

    def _compute_running_contract(self):
        contract_obj = self.env["package.contract"]
        res = super(HotelRegistration, self)._compute_running_contract()
        for hotel in self:
            running_contract = contract_obj.search_count(
                [("hotel_id", "=", hotel.id), ("state", "=", "open")]
            )
            if running_contract >= 1:
                hotel.update({"is_contract_running": True})
        return res

    room_line_ids = fields.One2many("hotel.room.line", "hotel_id", string="Hotel Rooms")
    facilities_ids = fields.Many2many("hotel.facilities", string="Hotel Facilities")
    hotel_contract_count = fields.Integer(
        "Hotel Contract", compute="_compute_hotel_contract_count"
    )
    is_hotel = fields.Boolean("Hotelling Service")
    registration_type = fields.Selection(
        selection_add=[("hotel", "Hotel")], ondelete={"hotel": "cascade"}
    )
    hotel_contract_ids = fields.One2many(
        "package.contract", "hotel_id", "Hotel Contracts"
    )

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        domain = domain or []
        context = dict(self._context) or {}
        if context.get("city_id") and context.get("package_contract_type") == "hotel":
            domain = [
                ("city_id", "=", context.get("city_id")),
                ("registration_type", "=", "hotel"),
                ("is_hotel", "=", True),
            ]
        return super()._search(domain, offset, limit, order, access_rights_uid)