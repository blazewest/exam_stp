
from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError



class Partner(models.Model):
    _inherit = "res.partner"

    name_donvi = fields.Char(string='Tên đơn vị', required=False)
    cccd = fields.Char(string='Số Cccd', required=False)
    tai_khoan = fields.Char(string='Tên tài khoản', required=False)
