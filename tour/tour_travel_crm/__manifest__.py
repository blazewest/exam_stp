#  See LICENSE file for full copyright and licensing details.
{
    "name": "Tours & Travels CRM",
    "version": "17.0.1.0.1",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "sequence": 1,
    "license": "AGPL-3",
    "category": "Tours & Travels",
    "website": "http://www.serpentcs.com",
    "summary": """
       Tours & Travels CRM
    """,
    "depends": ["crm", "tour_travel_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/crm_data.xml",
        "views/crm_lead_view.xml",
    ],
    "images": ["static/description/Banner_Tours_Travels_CRM.png"],
    "installable": True,
    "price": 45,
    "currency": "EUR",
}
