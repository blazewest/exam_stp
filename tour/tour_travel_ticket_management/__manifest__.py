#  See LICENSE file for full copyright and licensing details.
{
    "name": "Tours & Travels Ticket Management",
    "version": "17.0.1.0.1",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "sequence": 1,
    "license": "AGPL-3",
    "category": "Tours & Travels",
    "website": "http://www.serpentcs.com",
    "summary": """
        Tours & Travels Ticket Management
    """,
    "depends": ["tour_travel_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_view.xml",
        "views/ticket_view.xml",
        "views/tour_registration_view.xml",
        "report/report_quotation_ticket_package.xml",
    ],
    "images": ["static/description/Banner_tour_travel_ticket_management.png"],
    "demo": ["demo/ticketing_data.xml"],
    "installable": True,
    "application": True,
    "price": 65,
    "currency": "EUR",
}
