from odoo import api, fields, models
from odoo.exceptions import ValidationError

class SurveyClassification(models.Model):
    _name = 'survey.classification'
    _description = 'Survey Classification'

    name = fields.Char(string='Tên phân loại', required=True)
    min_score = fields.Float(string='Điểm tối thiểu', required=True)
    max_score = fields.Float(string='Điểm tối đa', required=True)
    survey_id = fields.Many2one('survey.survey', string='Bài kiểm tra', required=True)

    @api.constrains('min_score', 'max_score', 'survey_id')
    def _check_score_range(self):
        for record in self:
            survey = record.survey_id

            # Kiểm tra nếu xếp loại theo % thì max_score phải <= 100

            if (survey.is_percentage_based and (
                    record.max_score > 100 or record.min_score < 0)) or record.min_score > record.max_score:
                raise ValidationError(
                    "Khi xếp loại theo phần trăm, điểm tối thiểu phải >= 0 và điểm tối đa phải <= 100." if survey.is_percentage_based
                    else "Điểm tối đa phải lớn hơn điểm tối thiểu."
                )

            # Tìm các bản ghi khác có cùng survey_id
            overlapping_classifications = self.search([
                ('survey_id', '=', record.survey_id.id),
                ('id', '!=', record.id),
            ])

            for other_record in overlapping_classifications:
                if (record.min_score >= other_record.min_score and record.min_score <= other_record.max_score) or \
                        (record.max_score >= other_record.min_score and record.max_score <= other_record.max_score):
                    raise ValidationError(
                        "Phạm vi điểm của phân loại này giao nhau với bản ghi khác."
                    )

            # Đảm bảo rằng min_score của bản ghi hiện tại lớn hơn max_score của các bản ghi trước đó
            previous_classification = self.search([
                ('survey_id', '=', record.survey_id.id),
                ('id', '!=', record.id),
                ('max_score', '<', record.min_score)
            ], order='max_score desc', limit=1)

            if previous_classification and record.min_score <= previous_classification.max_score:
                raise ValidationError(
                    "Điểm tối thiểu của bản ghi phải lớn hơn điểm tối đa của phân loại trước đó (phải lớn hơn {0}).".format(
                        previous_classification.max_score
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SurveyClassification, self).create(vals_list)
        for record in records:
            self._create_or_update_tong_hop_diem(record)
        return records

    def write(self, vals):
        res = super(SurveyClassification, self).write(vals)
        for record in self:
            self._create_or_update_tong_hop_diem(record)
        return res

    def _create_or_update_tong_hop_diem(self, record):
        # Kiểm tra xem có bản ghi 'tong.hop.diem' nào tương ứng với 'survey.classification' hiện tại hay không
        tong_hop_diem = self.env['tong.hop.diem'].search([
            ('name', '=', record.name),
            ('cuoc_thi', '=', record.survey_id.id)
        ], limit=1)

        # Nếu tồn tại bản ghi 'tong.hop.diem', cập nhật nó
        if tong_hop_diem:
            tong_hop_diem.write({
                'name': record.name,
                'cuoc_thi': record.survey_id.id,
                'ghi_chu': f'{record.min_score} - {record.max_score}'
            })
        else:
            # Nếu chưa tồn tại, tạo mới
            self.env['tong.hop.diem'].create({
                'name': record.name,
                'cuoc_thi': record.survey_id.id,
                'ghi_chu': f'{record.min_score} - {record.max_score}'
            })
