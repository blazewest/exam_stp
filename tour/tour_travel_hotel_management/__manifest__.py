#  See LICENSE file for full copyright and licensing details.
{
    "name": "Tours & Travels Hotel Management",
    "version": "17.0.1.0.1",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "sequence": 1,
    "license": "AGPL-3",
    "category": "Tours & Travels",
    "website": "http://www.serpentcs.com",
    "summary": """
        Tours & Travels Hotel Management
    """,
    "depends": ["tour_travel_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/hotel_view.xml",
        "views/hotel_facilities_view.xml",
        "views/hotel_room_view.xml",
        "views/tour_package_view.xml",
        "views/package_contract_view.xml",
        "views/tour_registration_view.xml",
        "report/report_hotel_quotation_package.xml",
        "report/report_hotel_agreement.xml",
    ],
    "images": ["static/description/Banner_Tours_Travels_Hotel_Management.png"],
    "demo": ["demo/hotel_data.xml"],
    "installable": True,
    "application": True,
    "price": 65,
    "currency": "EUR",
    "assets": {
        "web.assets_backend": [
            # "tour_travel_hotel_management/static/**/*",
        ],
        "web.assets_qweb": [
            # "tour_travel_hotel_management/static/src/xml/image.xml",
        ],
    },
}
