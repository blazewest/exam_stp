
from odoo import fields, models, api
from itertools import groupby

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

    @api.depends('state')
    def _compute_diem_cao_nhat(self):
        for record in self:
            if record.state == 'done':
                if record.partner_id and record.survey_id:
                    # Tìm tất cả các bản ghi có cùng survey_id và partner_id
                    user_inputs = self.env['survey.user_input'].search([
                        ('survey_id', '=', record.survey_id.id),
                        ('partner_id', '=', record.partner_id.id),
                        ('state', '=', 'done')
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
            else:
                pass

    @api.depends('state')
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

            # Nếu bản ghi test_entry là False thì tiếp tục
            if not record.test_entry:
                # Tìm tất cả bản ghi `survey.user_input` có test_entry là False và có survey_id tương ứng
                all_user_inputs = self.env['survey.user_input'].search([
                    ('survey_id', '=', record.survey_id.id),
                    ('test_entry', '=', False)
                ])

                # Sắp xếp `all_user_inputs` theo `partner_id` để dùng `groupby`
                all_user_inputs_sorted = sorted(all_user_inputs, key=lambda r: r.partner_id.id)

                # Lấy một bản ghi duy nhất cho mỗi `partner_id`
                unique_user_inputs = [next(g) for _, g in
                                      groupby(all_user_inputs_sorted, key=lambda r: r.partner_id.id)]

                # Tìm tất cả bản ghi `tong.hop.diem` tương ứng với `cuoc_thi`
                tong_hop_diems = self.env['tong.hop.diem'].search([
                    ('cuoc_thi', '=', record.survey_id.id)
                ])

                # Cập nhật `tong` cho tất cả các bản ghi `tong.hop.diem`
                tong_hop_diems.write({'tong': len(unique_user_inputs)})

                # Cập nhật `so_lieu1` và `so_lieu2` cho các bản ghi phù hợp với `xep_loai`
                for tong_hop_diem in tong_hop_diems:
                    matching_user_inputs = filter(lambda r: r.xep_loai == tong_hop_diem.name, unique_user_inputs)
                    so_lieu1_count = len(list(matching_user_inputs))
                    tong_hop_diem.write({
                        'so_lieu1': so_lieu1_count,
                        'so_lieu2': (so_lieu1_count / tong_hop_diem.tong * 100) if tong_hop_diem.tong > 0 else 0
                    })

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

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SurveyUserInput, self).create(vals_list)
        return records

    def write(self, vals):
        res = super(SurveyUserInput, self).write(vals)
        return res

    def _update_tong_hop_diem(self):
        for record in self:
            # Chỉ tiếp tục nếu bản ghi `survey.user_input` có `state` là `done` và `test_entry` khác `False`
            if record.test_entry is False and record.xep_loai:
                # Tìm tất cả bản ghi `tong.hop.diem` tương ứng với `cuoc_thi`
                tong_hop_diems = self.env['tong.hop.diem'].search([
                    ('cuoc_thi', '=', record.survey_id.id)
                ])

                # Tìm bản ghi tương ứng với `xep_loai`
                matched_tong_hop_diem = tong_hop_diems.filtered(lambda r: r.name == record.xep_loai)

                # Tăng trường `tong` lên 1 cho tất cả bản ghi `tong.hop.diem`
                tong_hop_diems.write({'tong': tong_hop_diems.mapped('tong')[0] + 1})

                # Tăng trường `so_lieu1` và cập nhật `so_lieu2` cho bản ghi phù hợp
                if matched_tong_hop_diem:
                    matched_tong_hop_diem.write({
                        'so_lieu1': matched_tong_hop_diem.so_lieu1 + 1,
                        'so_lieu2': (matched_tong_hop_diem.so_lieu1 + 1) / matched_tong_hop_diem.tong * 100
                    })


