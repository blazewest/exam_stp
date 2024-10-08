#  See LICENSE file for full copyright and licensing details.
{
    "name": "Tours & Travels Meal Management",
    "version": "17.0.1.0.1",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "sequence": 1,
    "license": "AGPL-3",
    "category": "Tours & Travels",
    "website": "http://www.serpentcs.com",
    "summary": """
        Tours & Travels Meal Management
    """,
    "depends": ["tour_travel_hotel_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/meal_registration_view.xml",
        "views/meal_package_view.xml",
        "views/package_contract_view.xml",
        "views/tour_registration_view.xml",
        "report/report_quotation_restaurant_package.xml",
        "report/report_restaurant_agreement.xml",
    ],
    "images": [
        "static/description/Banner_tour_travel_meal_management.png"
    ],
    "demo": ["demo/meal_data.xml"],
    "installable": True,
    "application": True,
    "price": 65,
    "currency": "EUR",
}
