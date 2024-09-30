
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    survey_type = fields.Selection(selection_add=[
        ('survey', 'Survey'),
        ('assessment', 'Kiểm tra'),
    ],
        string='Survey Type', required=True, default='assessment')
    limit_question = fields.Integer(string='Số lượng câu hỏi')
    bool_setting = fields.Boolean('Cấu hình câu hỏi', default=False)
    qty_de = fields.Integer(string='Số lượng câu hỏi dễ')
    qty_tb = fields.Integer(string='Số lượng câu hỏi trung bình')
    qty_kho = fields.Integer(string='Số lượng câu hỏi khó')
    category_group_ids = fields.Many2many('category.question', string='Lĩnh vực câu hỏi')
    is_percentage_based = fields.Boolean(string="Xếp loại điểm theo %", default=True, help="Tích vào thì dựa theo % mà xếp loại, không tích thì dựa theo điểm số")
    classification_ids = fields.One2many(
        'survey.classification', 'survey_id', string='Xếp loại điểm'
    )

    @api.constrains('bool_setting', 'limit_question', 'qty_de', 'qty_tb', 'qty_kho')
    def _check_question_settings(self):
        if self.bool_setting:
            # Kiểm tra tổng số lượng câu hỏi có bằng limit_question không
            total_questions = self.qty_de + self.qty_tb + self.qty_kho
            if total_questions != self.limit_question:
                raise ValidationError(
                    "Tổng số lượng câu hỏi (dễ, trung bình, khó) phải bằng với giá trị của 'Số lượng câu hỏi'."
                )

            # Kiểm tra các trường qty_de, qty_tb, qty_kho không được âm
            if any(qty < 0 for qty in [self.qty_de, self.qty_tb, self.qty_kho]):
                raise ValidationError(
                    "Số lượng câu hỏi (dễ, trung bình, khó) không được mang giá trị âm."
                )

    @api.model_create_multi
    def create(self, vals_list):
        # Tạo bản ghi trong survey.survey
        survey = super(SurveySurvey, self).create(vals_list)

        # Kiểm tra nếu chưa có dữ liệu xếp loại (classification_ids)
        if not survey.classification_ids:
            # Tạo các bản ghi mặc định cho trường classification_ids
            default_classifications = [
                {
                    'name': 'Không đạt',
                    'min_score': 0.0,
                    'max_score': 49.9,
                    'survey_id': survey.id
                },
                {
                    'name': 'Trung bình',
                    'min_score': 50.0,
                    'max_score': 69.9,
                    'survey_id': survey.id
                },
                {
                    'name': 'Khá',
                    'min_score': 70.0,
                    'max_score': 99.4,
                    'survey_id': survey.id
                },
                {
                    'name': 'Xuất sắc',
                    'min_score': 99.5,
                    'max_score': 100.0,
                    'survey_id': survey.id
                }
            ]

            # Tạo các bản ghi classification mặc định
            for classification in default_classifications:
                self.env['survey.classification'].create(classification)

        return survey

    def _prepare_survey_render_values(self, survey, answer, **kwargs):
        # Get the existing user responses for this answer
        question_answers = {line.question_id.id: True for line in answer.user_input_line_ids}

        # Pass question_answers dictionary to the template
        return {
            'survey': survey,
            'answer': answer,
            'question_answers': question_answers,  # Add this to track answered questions
            # Other context variables...
        }


