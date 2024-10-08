#  See LICENSE file for full copyright and licensing details.
from datetime import datetime

from odoo import fields, models


class PassengerList(models.TransientModel):
    _name = "wizzard.passenger.list"
    _description = "Passenger List"

    type_of_package = fields.Selection(
        [("specific", "Specific"), ("nonspecific", "Non-Specific")],
        string="Tour Duration",
        required=True,
        default="specific",
    )
    registration_start_date = fields.Date(
        "Start Date",
    )
    registration_end_date = fields.Date(
        "End Date",
    )
    package_id = fields.Many2one(
        "sale.order.template",
        required=True,
        string="Package",
    )

    def package_passenger_list(self):
        if self.package_id:
            passenger = []
            data = {}
            if self.type_of_package == "nonspecific":
                start_date = datetime.combine(
                    self.registration_start_date, datetime.min.time()
                )
                end_date = datetime.combine(
                    self.registration_end_date, datetime.max.time()
                )
                domain = [
                    ("sale_order_template_id", "=", self.package_id.id),
                    ("state", "=", "sale"),
                    ("date_order", ">=", start_date),
                    ("date_order", "<=", end_date),
                ]
            else:
                domain = [
                    ("sale_order_template_id", "=", self.package_id.id),
                    ("state", "=", "sale"),
                ]

            registrations = self.env["sale.order"].search(domain)
            for registration in registrations:
                for passengers in registration.passenger_ids:
                    passenger.append(passengers.id)
            data["passengers"] = passenger
            data["package_id"] = self.package_id
            datas = {
                "ids": [],
                "model": "travellers.list",
                "form": data,
            }
            return self.env.ref(
                "tour_travel_management.action_total_passenger_list"
            ).report_action([], data=datas)
