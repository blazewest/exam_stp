from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DonVi(models.Model):
    _name = 'donvi'
    _description = 'Tên Đơn Vị'

    name = fields.Char(string='Tên Đơn Vị')
    code = fields.Char(string='Mã Đơn Vị')
    dia_chi = fields.Char(string='Địa chỉ Đơn Vị')

    @api.constrains('name', 'code')
    def _check_unique_name_and_code(self):
        for record in self:
            # Kiểm tra trùng tên đơn vị
            existing_name = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if existing_name:
                raise ValidationError("Tên đơn vị '%s' đã tồn tại." % record.name)

            # Kiểm tra trùng mã đơn vị
            existing_code = self.search([('code', '=', record.code), ('id', '!=', record.id)], limit=1)
            if existing_code:
                raise ValidationError("Mã đơn vị '%s' đã tồn tại." % record.code)