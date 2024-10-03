from odoo import models, fields, api

class DonVi(models.Model):
    _name = 'donvi'
    _description = 'Tên Đơn Vị'

    name = fields.Char(string='Tên Đơn Vị')
    code = fields.Char(string='Mã Đơn Vị')
    dia_chi = fields.Char(string='Địa chỉ Đơn Vị')
