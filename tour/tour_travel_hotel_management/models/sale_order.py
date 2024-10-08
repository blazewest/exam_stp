#  See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"
    
    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        domain = domain or []
        context = dict(self._context) or {}
        if context.get("city_id"):
            if (context.get("from_date") and context.get("to_date")) or context.get(
                "sale_order_template_id"
            ):
                package = self.env["sale.order.template"].search_read(
                    [("id", "=", self._context.get("sale_order_template_id"))],
                    ["type_of_package", "package_create_date"],
                )
                contracts = False
                if package and package[0].get("type_of_package") != "nonspecific":
                    contracts = self.env["package.contract"].search(
                        [
                            ("package_contract_type", "=", "hotel"),
                            ("date_start", "<=", context.get("from_date")),
                            ("date_end", ">=", context.get("to_date")),
                            ("date_start", "<=", context.get("from_date")),
                            ("date_end", ">=", context.get("to_date")),
                        ]
                    )
                if package and package[0].get("type_of_package") == "nonspecific":
                    contracts = self.env["package.contract"].search(
                        [
                            ("package_contract_type", "=", "hotel"),
                            ("date_start", "<=", package[0].get("package_create_date")),
                            ("date_end", ">=", package[0].get("package_create_date")),
                        ]
                    )
                if not package:
                    domain.append(["city_id", "in", [context.get("city_id")]])
                if contracts:
                    hotels = contracts.filtered(
                        lambda a: a.hotel_id.city_id.id == context.get("city_id")
                    ).mapped("hotel_id")
                    domain.append(["id", "in", hotels.ids])
            else:
                domain.append(["city_id", "in", [context.get("city_id")]])
        return super()._search(domain, offset, limit, order, access_rights_uid)

class SaleOrderTemplete(models.Model):
    _inherit = "sale.order.template"

    def get_cost_price(self):
        res = super(SaleOrderTemplete, self).get_cost_price()
        hotel_price = 0.0
        for order in self:
            hotel_price = sum(
                [
                    hotel_line.cost_price * hotel_line.stay_days
                    for hotel_line in order.hotel_package_line_ids
                    if hotel_line.room_type_id.capacity != 0
                ]
            )
        return res + hotel_price

    def get_cost_price_child(self):
        res = super(SaleOrderTemplete, self).get_cost_price_child()
        hotel_price = 0.0
        for order in self:
            hotel_price = sum(
                [
                    hotel_line.cost_price
                    * hotel_line.contract_id.cost_percentage_child
                    * hotel_line.stay_days
                    / 100
                    for hotel_line in order.hotel_package_line_ids
                    if hotel_line.room_type_id.capacity != 0 and hotel_line.contract_id
                ]
            )
        return res + hotel_price

    def get_sell_price(self):
        res = super(SaleOrderTemplete, self).get_sell_price()
        hotel_sell_price = 0.0
        for order in self:
            hotel_sell_price = sum(
                [
                    hotel_line.price_unit * hotel_line.stay_days
                    for hotel_line in order.hotel_package_line_ids
                    if hotel_line.room_type_id.capacity != 0
                ]
            )
        return res + hotel_sell_price

    def get_sell_price_child(self):
        res = super(SaleOrderTemplete, self).get_sell_price_child()
        hotel_sell_price = 0.0
        for order in self:
            hotel_sell_price = sum(
                [
                    hotel_line.price_unit
                    * hotel_line.contract_id.cost_percentage_child
                    * hotel_line.stay_days
                    / 100
                    for hotel_line in order.hotel_package_line_ids
                    if hotel_line.room_type_id.capacity != 0 and hotel_line.contract_id
                ]
            )
        return res + hotel_sell_price

    @api.depends("hotel_package_line_ids.cost_price")
    def _compute_cost_per_person(self):
        for order in self:
            total_cost = self.get_cost_price()
            total_cost_child = self.get_cost_price_child()
            order.update(
                {"cost_per_person": total_cost, "cost_per_child": total_cost_child}
            )

    @api.depends("hotel_package_line_ids.cost_price")
    def _compute_sell_per_person(self):
        for order in self:
            total_sale_price = self.get_sell_price()
            total_sale_price_child = self.get_sell_price_child()
            order.update(
                {
                    "sell_per_person": total_sale_price,
                    "sell_per_child": total_sale_price_child,
                }
            )

    hotel_package_line_ids = fields.One2many(
        "hotel.package.line", "sale_order_templete_id", string="Hotel Package Lines"
    )

    def action_generate_itinerary_plan(self):
        res = super(SaleOrderTemplete, self).action_generate_itinerary_plan()
        hotel = []
        for line in self.hotel_package_line_ids:
            from_date = line.from_date
            to_date = line.to_date
            for itinerary in self.itinerary_ids:
                if from_date and to_date and self.type_of_package == "specific":
                    if from_date == to_date + relativedelta(days=+1):
                        break
                    while itinerary.itinerary_date == from_date:
                        hotel.append(line.id)
                        from_date = from_date + relativedelta(days=+1)
                        itinerary.hotel_ids = hotel
                        itinerary.description = itinerary.description
                elif (  
                    self.type_of_package == "nonspecific"
                    and self.fixed_tour_days
                    and not from_date
                    and not to_date
                ):
                    if line.day_selection == itinerary.days:
                        itinerary.hotel_ids = [(4, line.id)]
                        itinerary.description = itinerary.description
        return res

    def _cron_non_specific_price_update(self):
        "Inherited in other process"
        res = super(SaleOrderTemplete, self)._cron_non_specific_price_update()
        current_date = fields.Date.context_today(self)
        packages = self.search(
            [("type_of_package", "=", "nonspecific"), ("state", "=", "confirm")]
        )
        for rec in packages:
            for line in rec.hotel_package_line_ids:
                contrac_hotel = self.env["package.contract"].search(
                    [
                        ("hotel_id", "=", line.hotel_id.id),
                        ("package_contract_type", "=", "hotel"),
                        ("date_start", "<=", current_date),
                        ("date_end", ">=", current_date),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )

                if contrac_hotel and contrac_hotel.id != line.contract_id.id:
                    line.update({"contract_id": contrac_hotel.id})
                    line._onchange_room_type()
        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hotel_line_ids = fields.One2many(
        "tour.registration.line", "hotel_sale_id", "Hotel Lines"
    )

    @api.onchange("sale_order_template_id", "tour_begin_date", "tour_end_date")
    def _onchange_tour_nonspecific_duration(self):
        res = super(SaleOrder, self)._onchange_tour_nonspecific_duration()
        if (
            self.sale_order_template_id
            and self.sale_order_template_id.type_of_package == "nonspecific"
            and self.tour_begin_date
            and self.tour_end_date
        ):
            for line in self.hotel_line_ids:
                contrac_hotel = self.env["package.contract"].search(
                    [
                        ("hotel_id", "=", line.hotel_id.id),
                        ("package_contract_type", "=", "hotel"),
                        ("date_start", "<=", self.tour_begin_date),
                        ("date_end", ">=", self.tour_end_date),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
                if contrac_hotel:
                    line.update({"contract_id": contrac_hotel.id})
                    contract_line = line.contract_id.mapped(
                        "contract_lines_ids"
                    ).filtered(lambda a: a.room_id == line.room_type_id)
                    line.update(
                        {
                            "price_unit": (
                                (
                                    contract_line.sales_price
                                    or line.room_type_id.product_id.lst_price
                                )
                                / contract_line.capacity
                            ),
                            "purchase_price": (
                                (
                                    contract_line.unit_price
                                    or line.room_type_id.product_id.standard_price
                                )
                                / contract_line.capacity
                            ),
                        }
                    )
        return res

    def get_package_hotel_lines(self):
        package_lines = []
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
        for line in template.hotel_package_line_ids:
            data = {
                "name": line.display_name,
                "stay_days": 0,
                "display_type": line.display_type,
            }
            pax_qty = 1
            total_pax = self.adults + self.children
            if line.room_type_id and total_pax > 1:
                pax_qty = round(total_pax / line.room_type_id.capacity)
            if not line.display_type:
                data = {
                    "name": line.display_name or line.hotel_id.name,
                    "from_date": line.from_date,
                    "to_date": line.to_date,
                    "hotel_id": line.hotel_id.id,
                    "city_id": line.city_id.id,
                    "display_type": line.display_type or False,
                    "room_type_id": line.room_type_id.id,
                    "stay_days": line.stay_days,
                    "room_qty": line.qty * pax_qty,
                    "product_uom_qty": line.qty,
                    "purchase_price": line.cost_price,
                    "price_unit": line.price_unit,
                    "product_id": line.room_type_id.product_id.id,
                    "product_uom": line.room_type_id.product_id.uom_id.id,
                }
            package_lines.append((0, 0, data))
        return package_lines

    @api.onchange("sale_order_template_id")
    def onchange_sale_order_template_id(self):
        order_lines = self.get_package_hotel_lines()
        if self.hotel_line_ids: 
            self.hotel_line_ids = [(5,0,0)]
        
        self.update({"hotel_line_ids": order_lines})
        if self.sale_order_template_id.type_of_package == "nonspecific":
            self._onchange_tour_nonspecific_duration()
        for rec in self.hotel_line_ids:
            if not rec.display_type:
                rec._onchange_hotel_id()
                rec._onchange_room_qty()
                rec._compute_tax_id()
        return super(SaleOrder, self).onchange_sale_order_template_id()

    @api.onchange("adults", "children")
    def _onchange_adults_children(self):
        for line in self.hotel_line_ids:
            line.adults = self.adults
            line.children = self.children


class TourRegistrationLine(models.Model):
    _inherit = "tour.registration.line"

    @api.depends("from_date", "to_date")
    def _compute_no_days(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                rec.stay_days = (rec.to_date - rec.from_date).days

    from_date = fields.Date()
    to_date = fields.Date()
    hotel_sale_id = fields.Many2one("sale.order", "Order", ondelete="cascade")
    city_id = fields.Many2one("city.city", "City", index=True)
    hotel_id = fields.Many2one("res.partner", "Hotel", ondelete="restrict", index=True)
    room_type_id = fields.Many2one("hotel.room", "Room Type", ondelete="restrict")
    room_qty = fields.Integer(string="No of Room", default=1)
    stay_days = fields.Integer(
        compute="_compute_no_days", string="Duration", store=True
    )

    @api.model
    def create(self, vals):
        if "hotel_sale_id" in vals:
            sale = self.env["sale.order"].browse(vals["hotel_sale_id"])
            vals.update({"order_id": sale.id})
        return super(TourRegistrationLine, self).create(vals)

    @api.onchange("from_date", "to_date", "city_id")
    def _onchange_from_to_date(self):
        if self._context.get("sale_order_template_id"):
            package = self.env["sale.order.template"].search_read(
                [("id", "=", self._context.get("sale_order_template_id"))],
                ["type_of_package"],
            )
            if package and package[0].get("type_of_package") != "nonspecific":
                self.update(
                    {
                        "hotel_id": False,
                        "contract_id": False,
                        "room_type_id": False,
                        "name": "",
                    }
                )
        else:
            self.update(
                {
                    "hotel_id": False,
                    "contract_id": False,
                    "room_type_id": False,
                    "name": "",
                }
            )

    @api.onchange("hotel_id")
    def _onchange_hotel_id(self):
        change_contract = {"contract_id": False, "room_type_id": False}
        contract = False
        if self.hotel_id and self.from_date and self.to_date:
            contract = self.env["package.contract"].search(
                [
                    ("hotel_id", "=", self.hotel_id.id),
                    ("package_contract_type", "=", "hotel"),
                    ("date_start", "<=", self.from_date),
                    ("date_end", ">=", self.to_date),
                    ("date_start", "<=", self.from_date),
                    ("date_end", ">=", self.to_date),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
        if (
            self.hotel_id
            and self.hotel_sale_id.sale_order_template_id
            and self.hotel_sale_id.sale_order_template_id.type_of_package
            == "nonspecific"
            and self.hotel_sale_id.sale_order_template_id.package_create_date
        ):
            contract = self.env["package.contract"].search(
                [
                    ("hotel_id", "=", self.hotel_id.id),
                    ("package_contract_type", "=", "hotel"),
                    (
                        "date_start",
                        "<=",
                        self.hotel_sale_id.sale_order_template_id.package_create_date,
                    ),
                    (
                        "date_end",
                        ">=",
                        self.hotel_sale_id.sale_order_template_id.package_create_date,
                    ),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
        if contract:
            change_contract = {"contract_id": contract.id}
        self.update(change_contract)

    def _get_product_descripation(self):
        res = super(TourRegistrationLine, self)._get_product_descripation()
        if self.hotel_id and self.room_type_id:
            name = ""
            name += "Hotel : {},{}".format(self.hotel_id.name, self.city_id.name)
            name += "\n" + "Room Type: {}".format(self.room_type_id.name)
            name += "\n" + "Qty : {} => {} (Stays) * {} (Room Qty)".format(
                self.stay_days * self.room_qty,
                self.stay_days,
                self.room_qty,
            )
            return name
        return res

    @api.onchange("room_qty", "stay_days")
    def _onchange_room_qty(self):
        for rec in self:
            room_quantity = rec.room_qty
            contract = False
            if self.hotel_id and self.from_date and self.to_date:
                contract = self.env["package.contract"].search(
                    [
                        ("hotel_id", "=", self.hotel_id.id),
                        ("package_contract_type", "=", "hotel"),
                        ("date_start", "<=", self.from_date),
                        ("date_end", ">=", self.to_date),
                        ("date_start", "<=", self.from_date),
                        ("date_end", ">=", self.to_date),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
            if (
                self.hotel_id
                and self.hotel_sale_id.sale_order_template_id
                and self.hotel_sale_id.sale_order_template_id.type_of_package
                == "nonspecific"
                and self.hotel_sale_id.sale_order_template_id.package_create_date
            ):
                contract = self.env["package.contract"].search(
                    [
                        ("hotel_id", "=", self.hotel_id.id),
                        ("package_contract_type", "=", "hotel"),
                        (
                            "date_start",
                            "<=",
                            self.hotel_sale_id.sale_order_template_id.package_create_date,
                        ),
                        (
                            "date_end",
                            ">=",
                            self.hotel_sale_id.sale_order_template_id.package_create_date,
                        ),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
            if contract and self.hotel_sale_id.group_costing_id:
                adult_quantity = self.hotel_sale_id.adults
                children_quantity = self.hotel_sale_id.children
                room_quantity = adult_quantity + (
                    children_quantity * contract.cost_percentage_child / 100
                )
            rec.product_uom_qty = room_quantity * rec.stay_days
            rec.name = rec._get_product_descripation()

    def _get_hotel_contract_line(self):
        contract_line = self.contract_id.mapped("contract_lines_ids").filtered(
            lambda a: a.room_id == self.room_type_id
        )
        return contract_line

    def _get_contract_price(self):
        res = super(TourRegistrationLine, self)._get_contract_price()
        if self.room_type_id and self.contract_id:
            contract_line = self._get_hotel_contract_line()
            res = contract_line.sales_price / contract_line.capacity
        return res

    def _get_contract_cost_price(self):
        res = super(TourRegistrationLine, self)._get_contract_cost_price()
        if self.room_type_id and self.contract_id:
            contract_line = self._get_hotel_contract_line()
            res = contract_line.unit_price / contract_line.capacity
        return res

    @api.onchange("room_type_id")
    def _onchange_room_type(self):
        if self.room_type_id:
            self.update(
                {
                    "product_id": self.room_type_id.product_id.id,
                    "order_id": self.hotel_sale_id.id,
                }
            )
            self._onchange_room_qty()

    @api.constrains("from_date", "to_date")
    def _check_duration_range_hotel(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                if rec.from_date > rec.to_date:
                    raise ValidationError(
                        _("From date should be greater than to date!")
                    )
                elif fields.Date.context_today(rec) > rec.from_date:
                    raise ValidationError(
                        _("From date should be greater than current date!")
                    )
                elif not (
                    rec.order_id.tour_begin_date
                    <= rec.from_date
                    < rec.order_id.tour_end_date
                ) or not (
                    rec.order_id.tour_begin_date
                    < rec.to_date
                    <= rec.order_id.tour_end_date
                ):
                    raise ValidationError(
                        _("From date/To date should in between Arrival/Departure date!")
                    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    hotel_id = fields.Many2one("hotel.package.line", "Hotel")


class HotelPackageLine(models.Model):
    _name = "hotel.package.line"
    _description = "Hotel Package Line"

    @api.depends("sale_order_templete_id.type_of_package")
    def _compute_room_qty(self):
        for rec in self:
            rec.stay_days_nonspecific = 0
            if (
                rec.sale_order_templete_id
                and rec.sale_order_templete_id.type_of_package == "nonspecific"
            ):
                rec.stay_days_nonspecific = 1

    @api.depends(
        "from_date",
        "to_date",
        "stay_days_nonspecific",
        "sale_order_templete_id.type_of_package",
    )
    def _compute_no_days(self):
        for rec in self:
            if (
                rec.from_date
                and rec.to_date
                and rec.sale_order_templete_id.type_of_package == "specific"
            ):
                rec.stay_days = (rec.to_date - rec.from_date).days
            if (
                rec.stay_days_nonspecific
                and rec.sale_order_templete_id.type_of_package == "nonspecific"
            ):
                rec.stay_days = rec.stay_days_nonspecific

    @api.depends("qty", "price_unit", "stay_days")
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.qty * line.price_unit * line.stay_days

    name = fields.Text("Description", translate=True)
    hotel_id = fields.Many2one("res.partner", "Hotel")
    from_date = fields.Date()
    to_date = fields.Date()
    city_id = fields.Many2one("city.city", "City")
    state_id = fields.Many2one(
        "res.country.state",
        "State",
        related="sale_order_templete_id.state_id",
        store=True,)
    
    
    # made room_type_id field required because of blank fields: order_id and product_uom_qty , getting from room_type_id onchange methods.
    room_type_id = fields.Many2one("hotel.room", "Room Type",required=True)
    stay_days = fields.Integer(
        compute="_compute_no_days", string="Duration", readonly=True, store=True
    )
    qty = fields.Float("Room Qty", required=True, default=1.0)
    cost_price = fields.Float(required=True, digits="Product Price", default=0.0)
    price_unit = fields.Float(
        "Unit Price", required=True, digits="Product Price", default=0.0
    )
    price_subtotal = fields.Float(
        "Subtotal", compute="_compute_amount", readonly=True, store=True
    )
    currency_id = fields.Many2one(
        "res.currency", "Currency", default=lambda self: self.env.company.currency_id
    )
    sale_order_templete_id = fields.Many2one("sale.order.template", string="Sale Order")
    contract_id = fields.Many2one("package.contract", "Contract")
    display_type = fields.Selection(
        [("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
    sequence = fields.Integer()
    stay_days_nonspecific = fields.Integer("Stay Days", compute="_compute_room_qty")
    day_selection = fields.Many2one("day.selection", "Days Selection")

    @api.onchange("from_date", "to_date", "city_id")
    def _onchange_from_to_date(self):
        self.update(
            {"hotel_id": False, "contract_id": False, "room_type_id": False, "name": ""}
        )

    @api.constrains("from_date", "to_date")
    def _check_duration_range_hotel(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                if rec.from_date > rec.to_date:
                    raise ValidationError(
                        _("From date should be greater than to date!")
                    )
                elif fields.Date.context_today(rec) > rec.from_date:
                    raise ValidationError(
                        _("From date should be greater than current date!")
                    )
                elif not (
                    rec.sale_order_templete_id.arrival_date
                    <= rec.from_date
                    < rec.sale_order_templete_id.return_date
                ) or not (
                    rec.sale_order_templete_id.arrival_date
                    < rec.to_date
                    <= rec.sale_order_templete_id.return_date
                ):
                    raise ValidationError(
                        _("From date/To date should in between Arrival/Departure date!")
                    )

    @api.onchange("hotel_id")
    def _onchange_hotel_id(self):
        change_contract = {"contract_id": False, "room_type_id": False}
        if self.hotel_id and self.from_date and self.to_date:
            contract = self.env["package.contract"].search(
                [
                    ("hotel_id", "=", self.hotel_id.id),
                    ("package_contract_type", "=", "hotel"),
                    ("date_start", "<=", self.from_date),
                    ("date_end", ">=", self.from_date),
                    ("date_start", "<=", self.to_date),
                    ("date_end", ">=", self.to_date),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            change_contract = {"contract_id": contract.id}
        if (
            self.hotel_id
            and not self.from_date
            and not self.to_date
            and self._context.get("type_of_package") == "nonspecific"
            and self._context.get("nonspecific_date")
        ):
            contract = self.env["package.contract"].search(
                [
                    ("hotel_id", "=", self.hotel_id.id),
                    ("package_contract_type", "=", "hotel"),
                    ("date_start", "<=", self._context.get("nonspecific_date")),
                    ("date_end", ">=", self._context.get("nonspecific_date")),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            change_contract = {"contract_id": contract.id}
        self.update(change_contract)

    def _get_product_description(self):
        if self.hotel_id and self.room_type_id:
            name = ""
            name += "Hotel : {},{}".format(self.hotel_id.name, self.city_id.name)
            name += "\n" + "Room Type: {}".format(self.room_type_id.name)
            return name
        
    @api.onchange("hotel_id")
    def _onnchange_hotel_id(self):
        for rec in self:
            if rec.hotel_id:
                rec.name = ""
                rec.name += "Hotel : {},{}".format(rec.hotel_id.name, rec.city_id.name)
        self.update(
                {
                    "price_unit": 0.0,
                    "cost_price": 0.0,
                }
            )

    @api.onchange("room_type_id")
    def _onchange_room_type(self):
        if self.room_type_id:
            for rec in self:
                rec.name = rec._get_product_description()
        if self.room_type_id and self.contract_id:
            contract_line = self.contract_id.mapped("contract_lines_ids").filtered(
                lambda a: a.room_id == self.room_type_id
            )
            self.update(
                {
                    "price_unit": (
                        (
                            contract_line.sales_price
                            or self.room_type_id.product_id.lst_price
                        )
                        / contract_line.capacity
                    ),
                    "cost_price": (
                        (
                            contract_line.unit_price
                            or self.room_type_id.product_id.standard_price
                        )
                        / contract_line.capacity
                    ),
                }
            )


class PackageItinerary(models.Model):
    _inherit = "package.itinerary"

    hotel_ids = fields.Many2many("hotel.package.line", string="Hotel")
