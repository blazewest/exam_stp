#  See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        domain = domain or []
        context = dict(self._context) or {}
        if context.get("attraction_id"):
            services_line = self.env["attraction.service.line"].search(
                [("attraction_id", "=", context.get("attraction_id"))]
            )
            services = services_line.mapped("service_id")
            domain.append(["id", "in", services.ids])
        return super()._search(domain, offset, limit, order, access_rights_uid)


class AttractionPackageLine(models.Model):
    _name = "attraction.package.line"
    _description = "Attraction Package Line"

    name = fields.Text("Description", translate=True)
    date = fields.Date()
    city_id = fields.Many2one("city.city", "City")
    attraction_id = fields.Many2one("res.partner", "Attraction")
    service_id = fields.Many2one("product.product", "Service")
    qty = fields.Float(required=True, default=1.0)
    contact = fields.Char()
    currency_id = fields.Many2one(
        "res.currency", "Currency", default=lambda self: self.env.company.currency_id
    )
    price_unit = fields.Float("Rate", required=True, default=0.0)
    cost_price = fields.Float(required=True, default=0.0)
    price_subtotal = fields.Float(compute="_get_total_attraction",string="Subtotal")
    sale_order_templete_id = fields.Many2one("sale.order.template", "Sale Order")
    display_type = fields.Selection(
        [("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
    sequence = fields.Integer()
    day_selection = fields.Many2one("day.selection", "Days Selection")
    
    def _get_total_attraction(self):
        for rec in self:
            rec.price_subtotal=0.0
            if rec.qty and rec.price_unit:
                rec.price_subtotal = rec.qty * rec.price_unit

    @api.constrains("date")
    def _check_duration_range_attraction(self):
        for rec in self:
            if (
                rec.date
                and rec.sale_order_templete_id.arrival_date
                and rec.sale_order_templete_id.return_date
                and not (
                    rec.sale_order_templete_id.arrival_date
                    <= rec.date
                    <= rec.sale_order_templete_id.return_date
                )
            ):
                raise ValidationError(
                    _("The date should be in between the Arrival/Departure date!")
                )

    @api.onchange("service_id")
    def _onchange_service_id(self):
        if self.service_id:
            self.update(
                {
                    "name": self.service_id.display_name,
                    "price_unit": self.service_id.lst_price,
                    "cost_price": self.service_id.standard_price,
                }
            )


class SaleOrderTemplete(models.Model):
    _inherit = "sale.order.template"

    def get_cost_price(self):
        res = super(SaleOrderTemplete, self).get_cost_price()
        for order in self:
            attraction_price = sum(
                [line.cost_price for line in order.attraction_package_line_ids]
            )
        return res + attraction_price

    def get_cost_price_child(self):
        res = super(SaleOrderTemplete, self).get_cost_price_child()
        for order in self:
            attraction_price = sum(
                [line.cost_price for line in order.attraction_package_line_ids]
            )
        return res + attraction_price

    def get_sell_price(self):
        res = super(SaleOrderTemplete, self).get_sell_price()
        for order in self:
            attraction_price = sum(
                [
                    line.price_unit * line.qty
                    for line in order.attraction_package_line_ids
                    if line.qty != 0
                ]
            )
        return res + attraction_price

    def get_sell_price_child(self):
        res = super(SaleOrderTemplete, self).get_sell_price_child()
        for order in self:
            attraction_price = sum(
                [
                    line.price_unit * line.qty
                    for line in order.attraction_package_line_ids
                    if line.qty != 0
                ]
            )
        return res + attraction_price

    @api.depends("attraction_package_line_ids.cost_price")
    def _compute_cost_per_person(self):
        for order in self:
            total_cost = self.get_cost_price()
            total_cost_child = self.get_cost_price_child()
            order.update(
                {"cost_per_person": total_cost, "cost_per_child": total_cost_child}
            )

    @api.depends("attraction_package_line_ids.cost_price")
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

    attraction_package_line_ids = fields.One2many(
        "attraction.package.line", "sale_order_templete_id", "Attraction Package Lines"
    )
    terms = fields.Html()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    attraction_id = fields.Many2one("attraction.package.line", "Attraction")
