
from odoo import fields, models, api
from itertools import groupby

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    name = fields.Char(string='Name', required=False,compute='_compute_name', store=True)
    xep_loai = fields.Char(string='Xếp loại', required=False, readonly=True,compute='_compute_xep_loai', store=True,
                           help="Xếp loại đựa trên điểm cao nhất")
    partner_name_clean = fields.Char(string='Tên đối tác chuẩn hóa',compute='_compute_partner_name_clean',store=True
    )
    input_important = fields.Float(string='Số dự đoán',compute='_compute_input_important', store=True)

    @api.depends('partner_id.name')
    def _compute_partner_name_clean(self):
        for record in self:
            # Chuẩn hóa tên đối tác: loại bỏ khoảng trắng và chuyển thành chữ thường
            record.partner_name_clean = record.partner_id.name.strip().lower() if record.partner_id.name else ''


    @api.depends('state')
    def _compute_xep_loai(self):
        for record in self:
            record.xep_loai = self._get_classification(record)
            if not record.test_entry:
                unique_user_inputs = self._get_unique_user_inputs(record.survey_id)
                self._update_tong_hop_diem(record.survey_id, unique_user_inputs)

    def _get_classification(self, record):
        """
        Trả về xếp loại dựa trên is_percentage_based của survey và điểm số.
        """
        field_to_check = 'scoring_percentage' if record.survey_id.is_percentage_based else 'scoring_total'
        classification = self.env['survey.classification'].search([
            ('survey_id', '=', record.survey_id.id),
            ('min_score', '<=', getattr(record, field_to_check)),
            ('max_score', '>=', getattr(record, field_to_check))
        ], limit=1)

        return classification.name if classification else 'Chưa xếp loại'

    def _get_unique_user_inputs(self, survey_id):
        """
        Lấy tất cả các bản ghi `survey.user_input` có test_entry là False và trả về danh sách
        các bản ghi duy nhất dựa trên partner_id.
        """
        all_user_inputs = self.env['survey.user_input'].search([
            ('survey_id', '=', survey_id.id),
            ('test_entry', '=', False)
        ])

        # Sắp xếp và nhóm theo partner_id để lấy duy nhất một bản ghi cho mỗi partner
        all_user_inputs_sorted = sorted(all_user_inputs, key=lambda r: r.partner_id.id)
        unique_user_inputs = [next(g) for _, g in groupby(all_user_inputs_sorted, key=lambda r: r.partner_id.id)]

        return unique_user_inputs

    def _update_tong_hop_diem(self, survey_id, unique_user_inputs):
        """
        Cập nhật giá trị `tong`, `so_lieu1`, và `so_lieu2` cho các bản ghi `tong.hop.diem`
        dựa trên xếp loại của các bản ghi `survey.user_input`.
        """
        tong_hop_diems = self.env['tong.hop.diem'].search([
            ('cuoc_thi', '=', survey_id.id)
        ])

        tong_hop_diems.write({'tong': len(unique_user_inputs)})

        # Cập nhật `so_lieu1` và `so_lieu2` cho các bản ghi `tong.hop.diem`
        for tong_hop_diem in tong_hop_diems:
            matching_user_inputs = filter(lambda r: r.xep_loai == tong_hop_diem.name, unique_user_inputs)
            so_lieu1_count = len(list(matching_user_inputs))
            tong_hop_diem.write({
                'so_lieu1': so_lieu1_count,
                'so_lieu2': (so_lieu1_count / tong_hop_diem.tong * 100) if tong_hop_diem.tong > 0 else 0
            })

    @api.depends('survey_id')
    def _compute_name(self):
        for record in self:
            record.name = record.survey_id.title

    @api.depends('state')
    def _compute_input_important(self):
        for record in self:
            important_value = 0
            # Duyệt qua các bản ghi trong user_input_line_ids
            for line in record.user_input_line_ids:
                if line.question_id.important:
                    # Nếu question_id.important = True, gán giá trị value_numerical_box
                    important_value = line.value_numerical_box
                    break  # Thoát khỏi vòng lặp sau khi tìm thấy bản ghi thỏa mãn
            record.input_important = important_value


    @api.model_create_multi
    def create(self, vals_list):
        records = super(SurveyUserInput, self).create(vals_list)
        return records

    def write(self, vals):
        res = super(SurveyUserInput, self).write(vals)
        return res


