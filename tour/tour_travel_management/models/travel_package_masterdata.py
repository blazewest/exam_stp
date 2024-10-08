#  See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class PackageItinerary(models.Model):
    _name = "package.itinerary"
    _description = "Package Itinerary"

    sequence = fields.Char()
    itinerary_date = fields.Date()
    days = fields.Many2one("day.selection", "Days Selection")
    description = fields.Html()
    sale_order_template_id = fields.Many2one(
        "sale.order.template", "Sale Order Template", ondelete="restrict"
    )
    event_time = fields.Float("Time")
    display_sctions = fields.Char("Display Sections")
    name = fields.Char("Day")


class ProductCategory(models.Model):
    _inherit = "product.category"
    _description = "Product Category"

    type_travel_product = fields.Selection(
        [
            ("hotel", "Hotel"),
            ("transportation", "Transportation"),
            ("tickets", "Tickets"),
            ("ticketing", "Ticketing"),
            ("tour", "Tour"),
            ("meals", "Meals"),
            ("visa", "Visa"),
            ("guide", "Guide"),
            ("other", "Other"),
        ],
        string="Type",
    )


class CityCity(models.Model):
    _name = "city.city"
    _description = "City"

    name = fields.Char("City", required=True, index=True)
    state_id = fields.Many2one("res.country.state", "State", required=True, index=True)
    zip = fields.Char("Zip Code")


class GroupCosting(models.Model):
    _name = "group.costing.line"
    _description = "Group Costing Line"

    name = fields.Char("Description", required=True)
    sale_order_template_id = fields.Many2one(
        "sale.order.template", "Sale Order Template", ondelete="restrict"
    )
    currency_id = fields.Many2one(
        "res.currency", "Currency", default=lambda self: self.env.company.currency_id
    )
    number_of_adult = fields.Integer("Adult")
    number_of_children = fields.Integer("Children")
    sales_price = fields.Float()
    cost_price = fields.Float()
    sales_price_child = fields.Float(compute='get_sales_costing_price')
    sales_price_adult = fields.Float(compute='get_sales_costing_price')



    def get_sales_costing_price(self):
        for rec in self:
            rec.sales_price_child = round((
                + rec.number_of_children * rec.sale_order_template_id.sell_per_child
            ),2)
            rec.sales_price_adult = round((
                rec.number_of_adult * rec.sale_order_template_id.sell_per_person
            ),2)

    @api.onchange("number_of_adult", "number_of_children")
    def _onchange_adult_children(self):
        for rec in self:
            rec.cost_price = (
                rec.number_of_adult * rec.sale_order_template_id.cost_per_person
                + rec.number_of_children * rec.sale_order_template_id.cost_per_child
            )
            rec.sales_price = (
                rec.number_of_adult * rec.sale_order_template_id.sell_per_person
                + rec.number_of_children * rec.sale_order_template_id.sell_per_child
            )
