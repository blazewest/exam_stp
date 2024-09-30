from odoo import api, fields, models, tools, _


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    level_question = fields.Selection([
        ('de', 'Dễ'),
        ('tb', 'Trung Bình'),
        ('kho', 'Khó')], string='Mức độ câu hỏi', default='de', required=True)
    category_group_ids = fields.Many2many('category.question',string='Lĩnh vực câu hỏi')
    # survey_id = fields.Many2one('survey.survey', string='Survey', ondelete='cascade')
