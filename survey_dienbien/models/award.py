from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class Award(models.Model):
    _name = 'award'
    _description = 'Award'

    name = fields.Selection(
        [('giai_nhat', 'Giải Nhất'),
         ('giai_nhi', 'Giải Nhì'),
         ('giai_ba', 'Giải Ba'),
         ('khuyen_khich', 'Khuyến Khích')],
        string='Tên giải thưởng',
        required=True,  # Đảm bảo người dùng phải chọn một giá trị
        default='giai_nhat'  # Giá trị mặc định là 'Giải Nhất'
    )
    qty_award = fields.Integer(string='Số lượng giải thưởng')
    remaining_qty_award = fields.Integer(string='Số lượng giải thưởng còn lại', default=0, readonly=True)
    survey_id = fields.Many2one('survey.survey', string='Bài kiểm tra', ondelete='cascade')
    priority_level = fields.Integer(
        string='Mức độ ưu tiên',
        required=True,
        default=0,  # Giá trị mặc định là 0 (ưu tiên cao nhất)
        help="Mức độ ưu tiên từ 0 đến 10, với 0 là mức ưu tiên cao nhất."
    )

    @api.constrains('qty_award')
    def _check_qty_award(self):
        for record in self:
            if record.qty_award <= 0:
                raise ValidationError(_("Số lượng giải thưởng phải lớn hơn 0."))

    @api.constrains('name', 'survey_id')
    def _check_unique_name_per_survey(self):
        for record in self:
            duplicate_award = self.search([
                ('survey_id', '=', record.survey_id.id),
                ('name', '=', record.name),
                ('id', '!=', record.id)  # Loại bỏ bản ghi hiện tại
            ])
            if duplicate_award:
                raise ValidationError(_("Tên giải thưởng '%s' đã tồn tại cho bài kiểm tra này.") % record.name)

    @api.constrains('priority_level', 'survey_id')
    def _check_unique_priority_per_survey(self):
        for record in self:
            if not (0 <= record.priority_level <= 10):
                raise ValidationError(_("Mức độ ưu tiên phải nằm trong khoảng từ 0 đến 10."))

            duplicate_priority = self.search([
                ('survey_id', '=', record.survey_id.id),
                ('priority_level', '=', record.priority_level),
                ('id', '!=', record.id)  # Loại bỏ bản ghi hiện tại
            ])
            if duplicate_priority:
                raise ValidationError(_("Mức độ ưu tiên '%s' đã tồn tại cho bài kiểm tra này.") % record.priority_level)

    @api.model_create_multi
    def create(self, vals_list):
        """Đồng bộ hóa số lượng giải thưởng còn lại với số lượng giải thưởng khi tạo mới"""
        for vals in vals_list:
            vals['remaining_qty_award'] = vals.get('qty_award', 0)
        return super(Award, self).create(vals_list)


