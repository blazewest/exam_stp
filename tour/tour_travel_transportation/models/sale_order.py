#  See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models, Command
from odoo.exceptions import ValidationError

class TransportationPackageLine(models.Model):
    _name = "transportation.package.line"
    _description = "Transportation Package Line"

    @api.depends("price_unit")
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.qty * line.price_unit

    name = fields.Text("Description", translate=True)
    journey_date = fields.Date()
    source_id = fields.Many2one("city.city", "Source")
    destination_id = fields.Many2one("city.city", "Destination")
    transportation_id = fields.Many2one("res.partner", "Transportation")
    vehicle_id = fields.Many2one("transportation.vehicle", "Vehicle")
    price_unit = fields.Float(
        "Unit Price", required=True, digits="Product Price", default=0.0
    )
    currency_id = fields.Many2one(
        "res.currency", "Currency", default=lambda self: self.env.company.currency_id
    )
    cost_price = fields.Float(required=True, digits="Product Price", default=0.0)
    price_subtotal = fields.Float("Subtotal", compute="_compute_amount")
    sale_order_templete_id = fields.Many2one("sale.order.template", "Sale Order")
    contract_id = fields.Many2one("package.contract", "Contract")
    display_type = fields.Selection(
        [("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
    qty = fields.Float(required=True, default=1.0)
    sequence = fields.Integer()
    day_selection = fields.Many2one("day.selection", "Days Selection")

    @api.constrains("journey_date")
    def _check_duration_range_transportation(self):
        for rec in self:
            if rec.journey_date and not (
                rec.sale_order_templete_id.arrival_date
                <= rec.journey_date
                <= rec.sale_order_templete_id.return_date
            ):
                raise ValidationError(
                    _("Journey Date should in between Arrival/Departure date!")
                )

    @api.onchange("journey_date", "source_id")
    def _onchange_journey_date(self):
        self.transportation_id = False

    @api.onchange("transportation_id")
    def _onchange_transportation_id(self):
        self.vehicle_id = False
        if self.transportation_id and self.journey_date:
            contract = self.env["package.contract"].search(
                [
                    ("transportation_id", "=", self.transportation_id.id),
                    ("package_contract_type", "=", "transportation"),
                    ("date_start", "<=", self.journey_date),
                    ("date_end", ">=", self.journey_date),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            if contract:
                self.contract_id = contract.id
        if (
            self.transportation_id
            and not self.journey_date
            and self._context.get("type_of_package") == "nonspecific"
            and self._context.get("package_create_date")
        ):
            contract = self.env["package.contract"].search(
                [
                    ("transportation_id", "=", self.transportation_id.id),
                    ("package_contract_type", "=", "transportation"),
                    ("date_start", "<=", self._context.get("package_create_date")),
                    ("date_end", ">=", self._context.get("package_create_date")),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            if contract:
                self.contract_id = contract.id

    def _get_transport_description(self):
        if self.transportation_id and self.vehicle_id:
            name = ""
            name += "Journey : {} -> {}".format(
                self.source_id.name,
                self.destination_id.name,
            )
            name += "\n" + "Journey Date: %s" % (self.journey_date)
            name += "\n" + "Vehicle: %s" % (self.vehicle_id.name)
            return name
        
    

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            for rec in self:
                rec.name = rec._get_transport_description()
        if self.vehicle_id and self.contract_id and self._context.get("pax_number"):
            contract_line = self.contract_id.mapped(
                "transportation_contract_line_ids"
            ).filtered(lambda a: a.vehicle_id.id == self.vehicle_id.id)
            self.update(
                {
                    "price_unit": (
                        (
                            contract_line.sales_price
                            or self.vehicle_id.product_id.lst_price
                        )
                        / self._context.get("pax_number")
                    ),
                    "cost_price": (
                        (
                            contract_line.unit_price
                            or self.vehicle_id.product_id.standard_price
                        )
                        / self._context.get("pax_number")
                    ),
                }
            )


class SaleOrderTemplete(models.Model):
    _inherit = "sale.order.template"

    def get_cost_price(self):
        res = super(SaleOrderTemplete, self).get_cost_price()
        transportation_price = 0.0
        for order in self:
            transportation_price = sum(
                [
                    line.cost_price * line.qty
                    for line in order.transportation_package_line_ids
                    if order.pax_group != 0
                ]
            )
        return res + transportation_price

    def get_cost_price_child(self):
        res = super(SaleOrderTemplete, self).get_cost_price_child()
        transportation_price = 0.0
        for order in self:
            transportation_price = sum(
                [
                    line.cost_price
                    * line.contract_id.cost_percentage_child
                    * line.qty
                    / 100
                    for line in order.transportation_package_line_ids
                    if order.pax_group != 0 and line.contract_id
                ]
            )
        return res + transportation_price

    def get_sell_price(self):
        res = super(SaleOrderTemplete, self).get_sell_price()
        transportation_sell_price = 0.0
        for order in self:
            transportation_sell_price = sum(
                [
                    line.price_unit * line.qty
                    for line in order.transportation_package_line_ids
                    if order.pax_group != 0
                ]
            )
        return res + transportation_sell_price

    def get_sell_price_child(self):
        res = super(SaleOrderTemplete, self).get_sell_price_child()
        transportation_sell_price = 0.0
        for order in self:
            transportation_sell_price = sum(
                [
                    line.price_unit
                    * line.contract_id.cost_percentage_child
                    * line.qty
                    / 100
                    for line in order.transportation_package_line_ids
                    if order.pax_group != 0 and line.contract_id
                ]
            )
        return res + transportation_sell_price

    @api.depends("transportation_package_line_ids.cost_price")
    def _compute_cost_per_person(self):
        for order in self:
            total_cost = self.get_cost_price()
            total_cost_child = self.get_cost_price_child()
            order.update(
                {"cost_per_person": total_cost, "cost_per_child": total_cost_child}
            )

    @api.depends("transportation_package_line_ids.price_unit")
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

    transportation_package_line_ids = fields.One2many(
        "transportation.package.line",
        "sale_order_templete_id",
        "Transportation Package Lines",
    )

    def _cron_non_specific_price_update(self):
        "Inherited in other process"
        res = super(SaleOrderTemplete, self)._cron_non_specific_price_update()
        current_date = fields.Date.context_today(self)
        context = dict(self._context) or {}
        packages = self.search(
            [("type_of_package", "=", "nonspecific"), ("state", "=", "confirm")]
        )
        for rec in packages:
            for line in rec.transportation_package_line_ids:
                contract_transport = self.env["package.contract"].search(
                    [
                        ("transportation_id", "=", line.transportation_id.id),
                        ("package_contract_type", "=", "transportation"),
                        ("date_start", "<=", current_date),
                        ("date_end", ">=", current_date),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
                if contract_transport and contract_transport.id != line.contract_id.id:
                    line.update({"contract_id": contract_transport.id})
                    context.update({"pax_number": rec.pax_group})
                    line.with_context(**context)._onchange_vehicle_id()
        return res

    def action_generate_itinerary_plan(self):
        res = super(SaleOrderTemplete, self).action_generate_itinerary_plan()
        for line in self.transportation_package_line_ids:
            transport_date = line.journey_date
            for itinerary in self.itinerary_ids:
                name = itinerary.description
                if (
                    itinerary.itinerary_date == transport_date
                    and self.type_of_package == "specific"
                ):
                    itinerary.transport_ids = [(4, line.id)]
                    if line.name:
                        # name += "\n Transportation : {} \n".format(line.name)
                        itinerary.description = name
                elif (
                    self.type_of_package == "nonspecific"
                    and self.fixed_tour_days
                    and not transport_date
                ):
                    if line.day_selection == itinerary.days:
                        itinerary.transport_ids = [(4, line.id)]
                        if line.name:
                            # name += "\n Transportation : {} \n".format(line.name)
                            itinerary.description = name
        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    transportation_line_ids = fields.One2many(
        "tour.registration.line", "transportation_sale_id", "Transportation Lines"
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
            for line in self.transportation_line_ids:
                contrac_transportation = self.env["package.contract"].search(
                    [
                        ("transportation_id", "=", line.transportation_id.id),
                        ("package_contract_type", "=", "transportation"),
                        ("date_start", "<=", self.tour_begin_date),
                        ("date_end", ">=", self.tour_end_date),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
                if contrac_transportation:
                    line.update({"contract_id": contrac_transportation.id})

                    contract_line = line.contract_id.mapped(
                        "transportation_contract_line_ids"
                    ).filtered(lambda a: a.vehicle_id.id == line.vehicle_id.id)
                    line.update(
                        {
                            "price_unit": (
                                (
                                    contract_line.sales_price
                                    or line.vehicle_id.product_id.lst_price
                                )
                                / self.sale_order_template_id.pax_group
                            ),
                            "purchase_price": (
                                (
                                    contract_line.unit_price
                                    or line.vehicle_id.product_id.standard_price
                                )
                                / self.sale_order_template_id.pax_group
                            ),
                        }
                    )
        return res

    def get_package_transportation_lines(self):
        package_lines = []
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
        for line in template.transportation_package_line_ids:
            data = {"name": line.display_name, "display_type": line.display_type}
            pax_qty = 1
            total_pax = self.adults + self.children
            if total_pax > 1:
                pax_qty = total_pax
            if not line.display_type:
                data = {
                    "name": line.transportation_id.display_name,
                    "journey_date": line.journey_date,
                    "source_id": line.source_id.id,
                    "destination_id": line.destination_id.id,
                    "transportation_id": line.transportation_id.id,
                    "display_type": line.display_type,
                    "vehicle_id": line.vehicle_id.id,
                    "vehicle_qty": line.qty * pax_qty,
                    "product_uom_qty": line.qty,
                    "purchase_price": line.cost_price,
                    "price_unit": line.price_unit,
                    "product_id": line.vehicle_id.product_id.id,
                    "product_uom": line.vehicle_id.product_id.uom_id.id,
                }
            package_lines.append((0, 0, data))
        return package_lines

    @api.onchange("sale_order_template_id")
    def onchange_sale_order_template_id(self):
        context = dict(self._context) or {}
        order_lines = self.get_package_transportation_lines()
        if len(self.transportation_line_ids) > 0: 
            self.transportation_line_ids = [(5,0,0)]
        self.update({"transportation_line_ids": order_lines})
        if self.sale_order_template_id.type_of_package == "nonspecific":
            self._onchange_tour_nonspecific_duration()
        for rec in self.transportation_line_ids:
            if not rec.display_type:
                context.update({"trasport_onchnage": True})
                rec.with_context(**context)._onchange_transportation_id()
                rec._onchange_vehicle_qty()
                rec._compute_tax_id()
        return super(SaleOrder, self).onchange_sale_order_template_id()



class TourRegistrationLine(models.Model):
    _inherit = "tour.registration.line"

    transportation_sale_id = fields.Many2one(
        "sale.order", "Transportation Order", ondelete="cascade"
    )
    journey_date = fields.Date()
    source_id = fields.Many2one("city.city", "Source")
    destination_id = fields.Many2one("city.city", "Destination")
    transportation_id = fields.Many2one(
        "res.partner", "Transportation", ondelete="restrict", index=True
    )
    vehicle_id = fields.Many2one(
        "transportation.vehicle", "Vehicle", ondelete="restrict"
    )
    vehicle_qty = fields.Integer(default=1)

    @api.model
    def create(self, vals):
        if "transportation_sale_id" in vals:
            sale = self.env["sale.order"].browse(vals["transportation_sale_id"])
            vals.update({"order_id": sale.id})
        return super(TourRegistrationLine, self).create(vals)

    @api.onchange("journey_date", "source_id")
    def _onchange_journey_date(self):
        if self._context.get("sale_order_template_id"):
            package = self.env["sale.order.template"].search_read(
                [("id", "=", self._context.get("sale_order_template_id"))],
                ["type_of_package"],
            )
            if package and package[0].get("type_of_package") != "nonspecific":
                self.transportation_id = False
        else:
            self.transportation_id = False

    @api.onchange("transportation_id")
    def _onchange_transportation_id(self):
        if not self._context.get("trasport_onchnage"):
            self.vehicle_id = False
        if self.transportation_id and self.journey_date:
            contract = self.env["package.contract"].search(
                [
                    ("transportation_id", "=", self.transportation_id.id),
                    ("package_contract_type", "=", "transportation"),
                    ("date_start", "<=", self.journey_date),
                    ("date_end", ">=", self.journey_date),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            if contract:
                self.contract_id = contract.id
        if (
            self.transportation_id
            and self.transportation_sale_id.sale_order_template_id
            and self.transportation_sale_id.sale_order_template_id.type_of_package
            == "nonspecific"
            and self.transportation_sale_id.sale_order_template_id.package_create_date
        ):
            contract = self.env["package.contract"].search(
                [
                    ("transportation_id", "=", self.transportation_id.id),
                    ("package_contract_type", "=", "transportation"),
                    (
                        "date_start",
                        "<=",
                        self.transportation_sale_id.sale_order_template_id.package_create_date,
                    ),
                    (
                        "date_end",
                        ">=",
                        self.transportation_sale_id.sale_order_template_id.package_create_date,
                    ),
                    ("state", "=", "open"),
                ],
                limit=1,
            )
            if contract:
                self.update({"contract_id": contract.id})

    @api.onchange("vehicle_qty")
    def _onchange_vehicle_qty(self):
        for rec in self:
            vehical_quantity = rec.vehicle_qty
            contract = False
            if self.transportation_id and self.journey_date:
                contract = self.env["package.contract"].search(
                    [
                        ("transportation_id", "=", self.transportation_id.id),
                        ("package_contract_type", "=", "transportation"),
                        ("date_start", "<=", self.journey_date),
                        ("date_end", ">=", self.journey_date),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
            if (
                self.transportation_id
                and self.transportation_sale_id.sale_order_template_id
                and self.transportation_sale_id.sale_order_template_id.type_of_package
                == "nonspecific"
                and self.transportation_sale_id.sale_order_template_id.package_create_date
            ):
                contract = self.env["package.contract"].search(
                    [
                        ("transportation_id", "=", self.transportation_id.id),
                        ("package_contract_type", "=", "transportation"),
                        (
                            "date_start",
                            "<=",
                            self.transportation_sale_id.sale_order_template_id.package_create_date,
                        ),
                        (
                            "date_end",
                            ">=",
                            self.transportation_sale_id.sale_order_template_id.package_create_date,
                        ),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
            if contract and self.transportation_sale_id.group_costing_id:
                adult_quantity = self.transportation_sale_id.adults
                children_quantity = self.transportation_sale_id.children
                vehical_quantity = adult_quantity + (
                    children_quantity * contract.cost_percentage_child / 100
                )
            rec.product_uom_qty = vehical_quantity
            rec.name = rec._get_product_descripation() or rec.name

    def _get_product_descripation(self):
        res = super(TourRegistrationLine, self)._get_product_descripation()
        if self.transportation_id and self.vehicle_id:
            name = ""
            name += "Journey : {} -> {}".format(
                self.source_id.name,
                self.destination_id.name,
            )
            name += "\n" + "Journey Date: %s" % (self.journey_date)
            name += "\n" + "Vehicle: %s" % (self.vehicle_id.name)
            return name
        return res

    def _get_contract_price(self):
        res = super(TourRegistrationLine, self)._get_contract_price()
        if self.vehicle_id and self.contract_id:
            contract_line = self._get_transport_contract_line()
            res = contract_line.sales_price
        return res

    def _get_transport_contract_line(self):
        contract_line = self.contract_id.mapped(
            "transportation_contract_line_ids"
        ).filtered(lambda a: a.vehicle_id.id == self.vehicle_id.id)
        return contract_line

    def _get_contract_cost_price(self):
        res = super(TourRegistrationLine, self)._get_contract_cost_price()
        if self.vehicle_id and self.contract_id:
            contract_line = self._get_transport_contract_line()
            res = contract_line.unit_price / contract_line.capacity
        return res

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.update(
                {
                    "product_id": self.vehicle_id.product_id.id,
                    "order_id": self.transportation_sale_id.id,
                }
            )
            self._onchange_vehicle_qty()

    @api.constrains("journey_date")
    def _check_journey_date(self):
        if self.journey_date:
            if fields.Date.context_today(self) > self.journey_date:
                raise ValidationError(
                    _("Journey date should be greater than current date!")
                )
            elif not (
                self.order_id.tour_begin_date
                <= self.journey_date
                <= self.order_id.tour_end_date
            ):
                raise ValidationError(
                    _("Journey date should in between Arrival/Departure date!")
                )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    transportation_id = fields.Many2one("transportation.package.line", "Transportation")


class PackageItinerary(models.Model):
    _inherit = "package.itinerary"

    transport_ids = fields.Many2many(
        "transportation.package.line", string="Transportation"
    )
