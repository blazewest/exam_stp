#  See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    attraction_line_ids = fields.One2many(
        "tour.registration.line", "attraction_sale_id", "Attraction Lines"
    )
    term_rules = fields.Html(related="sale_order_template_id.terms")

    def get_package_attraction_lines(self):
        package_lines = []
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
        for line in template.attraction_package_line_ids:
            data = {
                "name": line.display_name,
                "display_type": line.display_type,
                "order_id": self.id,
            }
            pax_qty = 1
            total_pax = self.adults + self.children
            if total_pax > 1:
                pax_qty = total_pax
            if not line.display_type:
                data = {
                    "name": line.service_id.display_name,
                    "date": line.date,
                    "city_id": line.city_id.id,
                    "attraction_id": line.attraction_id.id,
                    "display_type": line.display_type,
                    "attraction_service_id": line.service_id.id,
                    "product_uom_qty": pax_qty,
                    "purchase_price": line.cost_price,
                    "price_unit": line.price_unit,
                    "product_id": line.service_id.id,
                    "product_uom": line.service_id.uom_id.id,
                }
            package_lines.append((0, 0, data))
        return package_lines

    @api.onchange("sale_order_template_id")
    def onchange_sale_order_template_id(self):
        res = super(SaleOrder, self).onchange_sale_order_template_id()
        attraction_order_lines = self.get_package_attraction_lines()
        self.attraction_line_ids = [(5, 0, 0)]
        self.update({"attraction_line_ids": attraction_order_lines})
        for rec in self.attraction_line_ids:
            if not rec.display_type:
                rec._compute_tax_id()
        return res


class TourRegistrationLine(models.Model):
    _inherit = "tour.registration.line"

    attraction_sale_id = fields.Many2one(
        "sale.order", "Attraction Order", ondelete="cascade"
    )
    date = fields.Date()
    city_id = fields.Many2one("city.city", "City")
    attraction_id = fields.Many2one(
        "res.partner", "Attraction", ondelete="restrict", index=True
    )
    attraction_service_id = fields.Many2one(
        "product.product", "Attraction Services", ondelete="restrict"
    )
    extra_ticket_sale_id = fields.Many2one(
        "sale.order", "Extra Ticket Order", ondelete="cascade"
    )
    ticket_id = fields.Many2one("product.product", "Tickets", ondelete="restrict")
    ticket_qty = fields.Integer(default=1)

    @api.model
    def create(self, vals):
        if "attraction_sale_id" in vals:
            sale = self.env["sale.order"].browse(vals["attraction_sale_id"])
            vals.update({"order_id": sale.id})
        return super(TourRegistrationLine, self).create(vals)

    @api.onchange("ticket_qty")
    def _onchange_extra_ticket_qty(self):
        for rec in self:
            rec.product_uom_qty = rec.ticket_qty

    @api.onchange("attraction_service_id")
    def _onchange_attraction_id(self):
        if self.attraction_service_id:
            self.update(
                {
                    "product_id": self.attraction_service_id.id,
                    "order_id": self.attraction_sale_id.id,
                }
            )

    @api.onchange("ticket_id")
    def _onchange_ticket_id(self):
        if self.ticket_id:
            self.update(
                {
                    "product_id": self.ticket_id.id,
                    "order_id": self.extra_ticket_sale_id.id,
                }
            )

    @api.constrains("date")
    def _check_journey_date(self):
        for rec in self:
            if rec.date:
                if fields.Date.context_today(self) > rec.date:
                    raise ValidationError(
                        _("Journey date should be greater than current date!")
                    )
                elif not (
                    rec.order_id.tour_begin_date
                    <= rec.date
                    <= rec.order_id.tour_end_date
                ):
                    raise ValidationError(
                        _("Journey date should in between Arrival/Departure date!")
                    )
