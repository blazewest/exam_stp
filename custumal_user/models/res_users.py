
from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    name_donvi = fields.Char(string='Tên đơn vị', required=False)
    cccd = fields.Char(string='Số Cccd', required=False)
    phone = fields.Char(string='Số điện thoại', required=False)
    function = fields.Char(string='Chức vụ', required=False)

    # Ghi đè phương thức create để đồng bộ với res.partner khi tạo mới res.users
    @api.model_create_multi
    def create(self, vals_list):
        # Gọi phương thức create của lớp cha để xử lý batch create
        users = super(ResUsers, self).create(vals_list)

        # Đồng bộ dữ liệu sang res.partner cho tất cả các bản ghi
        for user, vals in zip(users, vals_list):
            if user.partner_id:
                user.partner_id.write({
                    'name_donvi': vals.get('name_donvi', user.partner_id.name_donvi),
                    'cccd': vals.get('cccd', user.partner_id.cccd),
                    'phone': vals.get('phone', user.partner_id.phone),
                    'function': vals.get('function', user.partner_id.function),
                    'tai_khoan': vals.get('login', user.partner_id.tai_khoan),
                })

        return users

    def write(self, vals):
        # Ghi đè phương thức write để xử lý cho tất cả các bản ghi
        result = super(ResUsers, self).write(vals)

        # Đồng bộ dữ liệu sang res.partner cho tất cả các bản ghi
        for user in self:
            if user.partner_id:
                user.partner_id.write({
                    'name_donvi': vals.get('name_donvi', user.partner_id.name_donvi),
                    'cccd': vals.get('cccd', user.partner_id.cccd),
                    'phone': vals.get('phone', user.partner_id.phone),
                    'function': vals.get('function', user.partner_id.function),
                })

        return result
