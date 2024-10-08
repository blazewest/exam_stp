# See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    image_medium = fields.Binary("Medium-sized image")
    package_images = fields.One2many("package.image", "package_sale_id", "Images")

    def get_updated_package_price(self, start_date=None):
        sell_per_person = self.sell_per_person
        if start_date:
            sell_per_person = 0
            for rec in self:
                sell_per_person = rec.sell_per_person
                hotel_cost_total = rec.hotel_package_line_ids.mapped('price_subtotal')
                transportation_cost_total = rec.transportation_package_line_ids.mapped('price_subtotal')
                meal_package_line_total = rec.meal_package_line_ids.mapped('price_subtotal')
                hotel_price_lst = []
                meal_price_lst = []
                transportation_price_lst = []
                for line in rec.hotel_package_line_ids:
                    contrac_hotel = rec.env["package.contract"].search(
                                [
                                    ("hotel_id", "=", line.hotel_id.id),
                                    ("package_contract_type", "=", "hotel"),
                                    ("date_start", "<=", start_date),
                                    ("date_end", ">=", start_date),
                                    ("state", "=", "open")
                                ],
                                limit=1,
                            )
                    if contrac_hotel:
                        rooms_price = contrac_hotel.contract_lines_ids.filtered(
                            lambda a: a.room_id.id == line.room_type_id.id)
                        hotel_price_lst.append(rooms_price.sales_price/rooms_price.capacity)
                if sum(hotel_cost_total) != sum(hotel_price_lst):
                    sell_per_person = sell_per_person - sum(hotel_cost_total) + \
                                sum(hotel_price_lst)

                for line in rec.meal_package_line_ids:
                    contract_meal = rec.env["package.contract"].search(
                                [
                                    ("meal_id", "=", line.meal_id.id),
                                    ("package_contract_type", "=", "meal"),
                                    ("date_start", "<=", start_date),
                                    ("date_end", ">=", start_date),
                                    ("state", "=", "open")
                                ],
                                limit=1,
                            )

                    if contract_meal:
                        meal_price = contract_meal.meal_contract_lines_ids.filtered(
                            lambda a: a.meal_package_id.id == line.meal_package_id.id).sales_price
                        meal_price_lst.append(meal_price)
                if sum(meal_package_line_total) != sum(meal_price_lst):
                    sell_per_person = sell_per_person - sum(meal_package_line_total) + \
                                sum(meal_price_lst)

                for line in rec.transportation_package_line_ids:
                    contract_transport = rec.env["package.contract"].search(
                                [
                                    ("transportation_id", "=", line.transportation_id.id),
                                    ("package_contract_type", "=", "transportation"),
                                    ("date_start", "<=", start_date),
                                    ("date_end", ">=", start_date),
                                    ("state", "=", "open")
                                ],
                                limit=1,
                            )
                    if contract_transport:
                        transport_price = contract_transport.transportation_contract_line_ids.filtered(
                            lambda a: a.vehicle_id.id == line.vehicle_id.id).sales_price

                        transportation_price_lst.append(transport_price/rec.pax_group)
                if sum(transportation_cost_total) != sum(transportation_price_lst):
                    sell_per_person = sell_per_person - sum(transportation_cost_total) + \
                                sum(transportation_price_lst)
        return float(int(sell_per_person))

    def get_group_cost_package_price(self, start_date=None, group_line=None):
        sell_per_person = group_line.sales_price
        return '{:.2f}'.format(sell_per_person)
