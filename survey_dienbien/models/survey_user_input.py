
from odoo import fields, models, api

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    name = fields.Char(string='Name', required=False,compute='_compute_name', store=True)
    diem_cao_nhat = fields.Integer('Điểm cao nhất', readonly=True, compute='_compute_diem_cao_nhat', store=True)
    so_lan_lam = fields.Integer(string='Tổng số lượt thi', readonly=True, compute='_compute_so_lan_lam', store=True)
    xep_loai = fields.Char(string='Xếp loại', required=False, readonly=True,compute='_compute_xep_loai', store=True,
                           help="Xếp loại đựa trên điểm cao nhất")
    partner_name_clean = fields.Char(string='Tên đối tác chuẩn hóa',compute='_compute_partner_name_clean',store=True
    )

    @api.depends('partner_id.name')
    def _compute_partner_name_clean(self):
        for record in self:
            # Chuẩn hóa tên đối tác: loại bỏ khoảng trắng và chuyển thành chữ thường
            record.partner_name_clean = record.partner_id.name.strip().lower() if record.partner_id.name else ''

    @api.depends('partner_id', 'survey_id')
    def _compute_diem_cao_nhat(self):
        for record in self:
            if record.partner_id and record.survey_id:
                # Tìm tất cả các bản ghi có cùng survey_id và partner_id
                user_inputs = self.env['survey.user_input'].search([
                    ('survey_id', '=', record.survey_id.id),
                    ('partner_id', '=', record.partner_id.id)
                ])

                if user_inputs:
                    if record.survey_id.is_percentage_based:
                        # Tìm điểm cao nhất theo scoring_percentage
                        diem_cao_nhat = max(user_inputs.mapped('scoring_percentage'), default=0)
                    else:
                        # Tìm điểm cao nhất theo scoring_total
                        diem_cao_nhat = max(user_inputs.mapped('scoring_total'), default=0)

                    # Cập nhật trường diem_cao_nhat cho tất cả các bản ghi tìm được
                    user_inputs.write({'diem_cao_nhat': diem_cao_nhat})
            else:
                # Nếu không tìm thấy partner_id hoặc survey_id thì gán diem_cao_nhat = 0
                record.diem_cao_nhat = 0

    @api.depends('diem_cao_nhat', 'survey_id')
    def _compute_xep_loai(self):
        for record in self:
            classification = self.env['survey.classification'].search([
                ('survey_id', '=', record.survey_id.id),
                ('min_score', '<=', record.diem_cao_nhat),
                ('max_score', '>=', record.diem_cao_nhat)
            ], limit=1)

            if classification:
                record.xep_loai = classification.name
            else:
                record.xep_loai = 'Chưa xếp loại'

    @api.depends('partner_id', 'survey_id')
    def _compute_so_lan_lam(self):
        for record in self:
            if record.partner_id and record.survey_id:
                # Tìm tất cả các bản ghi có cùng partner_id và survey_id
                user_inputs = self.env['survey.user_input'].search([
                    ('partner_id', '=', record.partner_id.id),
                    ('survey_id', '=', record.survey_id.id)
                ])

                # Đếm tổng số lượt thi
                so_lan_lam = len(user_inputs)

                # Cập nhật trường so_lan_lam cho tất cả các bản ghi tìm được
                user_inputs.write({'so_lan_lam': so_lan_lam})
            else:
                # Nếu không có partner_id hoặc survey_id, gán so_lan_lam = 0
                record.so_lan_lam = 0

    @api.depends('survey_id')
    def _compute_name(self):
        for record in self:
            record.name = record.survey_id.title
