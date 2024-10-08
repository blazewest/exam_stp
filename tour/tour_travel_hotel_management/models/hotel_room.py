# See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MultiImages(models.Model):
    _name = "multi.images"
    _description = "Multi Images"

    image = fields.Binary("Images")
    description = fields.Char()
    title = fields.Char()
    hotel_room_id = fields.Many2one("hotel.room", "Room")


class HotelRoom(models.Model):
    _name = "hotel.room"
    _description = "Hotel Room"

    product_id = fields.Many2one(
        "product.product",
        " Hotel Room",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    max_adult = fields.Integer("Maximum Adult", default="1")
    max_child = fields.Integer("Maximum Children")
    capacity = fields.Integer("Total Capacity", compute='_compute_total_capacity',store=True)
    hotel_id = fields.Many2one("res.partner", "Hotel")
    multi_images = fields.One2many("multi.images", "hotel_room_id")
    # other_attachment_ids = fields.One2many(
    #     comodel_name='ir.attachment',
    #     inverse_name='tenancy_id',
    #     string='Attachments')

    @api.constrains("max_adult", "capacity")
    def _check_max_capacity(self):
        for rec in self:
            if rec.max_adult and rec.capacity and rec.capacity < rec.max_adult:
                raise ValidationError(
                    _("Number of Adults can not be more than room capacity.")
                )
                
    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        domain = domain or []
        context = dict(self._context) or {}
        if (
            context.get("from_date")
            and context.get("to_date")
            and context.get("hotel_id")
        ):
            domain = []
            contract = self.env["package.contract"].search(
                [
                    ("hotel_id", "=", context.get("hotel_id")),
                    ("package_contract_type", "=", "hotel"),
                    ("date_start", "<=", context.get("from_date")),
                    ("date_end", ">=", context.get("to_date")),
                    ("date_start", "<=", context.get("from_date")),
                    ("date_end", ">=", context.get("to_date")),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            rooms = (
                contract.filtered(lambda a: a.hotel_id.id == context.get("hotel_id"))
                .mapped("contract_lines_ids")
                .mapped("room_id")
            )
            domain.append(["id", "in", rooms.ids])
        if (
            not context.get("from_date")
            and not context.get("to_date")
            and context.get("hotel_id")
            and context.get("nonspecific_date")
        ):
            if context.get("type_of_package") == "nonspecific" or (
                context.get("sale_order_template_id")
                and self.env["sale.order.template"]
                .search_read(
                    [("id", "=", context.get("sale_order_template_id"))],
                    ["type_of_package"],
                )[0]
                .get("type_of_package")
                == "nonspecific"
            ):
                domain = []
                contract = self.env["package.contract"].search(
                    [
                        ("hotel_id", "=", context.get("hotel_id")),
                        ("package_contract_type", "=", "hotel"),
                        ("date_start", "<=", context.get("nonspecific_date")),
                        ("date_end", ">=", context.get("nonspecific_date")),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
                rooms = (
                    contract.filtered(
                        lambda a: a.hotel_id.id == context.get("hotel_id")
                    )
                    .mapped("contract_lines_ids")
                    .mapped("room_id")
                )
                domain.append(["id", "in", rooms.ids])
        return super()._search(domain, offset, limit, order, access_rights_uid)

    @api.depends('max_adult','max_child')
    def _compute_total_capacity(self):
        for record in self:
            record.capacity = record.max_adult + record.max_child

class HotelRoomType(models.Model):
    _name = "hotel.room.type"
    _description = "Hotel Room Type"

    name = fields.Char(required=True)


class HotelRoomLine(models.Model):
    _name = "hotel.room.line"
    _rec_name = "room_id"
    _description = "Hotel Room Line"

    hotel_id = fields.Many2one("res.partner", "Hotel", ondelete="cascade")
    room_id = fields.Many2one("hotel.room", "Room", ondelete="restrict", index=True)
    room_type_id = fields.Many2one("hotel.room.type", "Room Type", ondelete="restrict")
    capacity = fields.Integer("Total Capacity", required=True, default=1)
    room_qty = fields.Integer("No of Rooms")
    unit_price = fields.Float()
    cost_price = fields.Float()
    package_contract_id = fields.Many2one(
        "package.contract", "Contract", ondelete="cascade"
    )
    package_contract_type = fields.Selection(
        related="package_contract_id.package_contract_type", string="Type", store=True
    )

    @api.onchange("room_id")
    def _onchange_room_id(self):
        self.update(
            {
                "unit_price": self.room_id.list_price or 0,
                "cost_price": self.room_id.standard_price or 0,
                "capacity": self.room_id.capacity or 0,
            }
        )
