#  See LICENSE file for full copyright and licensing details.
{
    "name": "Tours & Travels Attraction Expenses",
    "version": "17.0.1.0.0",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "sequence": 1,
    "license": "AGPL-3",
    "category": "Tours & Travels",
    "website": "http://www.serpentcs.com",
    "summary": """
        Tours & Travels Attraction Expenses
    """,
    "depends": ["tour_travel_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_template_view.xml",
        "views/attraction_registration_view.xml",
        "report/report_quotation_attraction_package.xml",
    ],
    "demo": ["demo/attraction_data.xml"],
    "images": ["static/description/Banner_tour_travel_attraction_management.png"],
    "installable": True,
    "price": 65,
    "currency": "EUR",
}
