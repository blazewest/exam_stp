from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'


    access_mode = fields.Selection([
        ('public', 'Bất kỳ ai có liên kết'),
        ('token', 'Chỉ những người được mời')], string='Chế độ truy cập',
        default='public', required=True)


    def _get_all_child_categories(self, category):
        # Đệ quy để lấy tất cả danh mục con của một danh mục
        all_child_categories = category.child_ids
        for child in category.child_ids:
            all_child_categories |= self._get_all_child_categories(child)
        return all_child_categories

    def action_check_questions_availability(self):
        if not self.category_group_ids:
            raise ValidationError(
                "Trường Lĩnh vực câu hỏi đang để trống, không thể thực hiện kiểm tra"
            )
            return False

        # Lấy tất cả các danh mục cha và con
        all_categories = self.category_group_ids
        for category in self.category_group_ids:
            all_categories |= self._get_all_child_categories(category)

        if self.bool_setting:
            required_questions = {
                'de': self.qty_de,
                'tb': self.qty_tb,
                'kho': self.qty_kho,
            }
            # Kiểm tra số lượng câu hỏi trong kho
            for level, required_qty in required_questions.items():
                available_questions = self.env['question.bank'].search_count([
                    ('category_group_ids', 'in', all_categories.ids),
                    ('level_question', '=', level),
                ])
                if available_questions < required_qty:
                    raise ValidationError(
                        f"Số lượng câu hỏi mức '{level}' không đủ. "
                        f"Cần {required_qty}, nhưng chỉ có {available_questions} câu hỏi."
                    )
                    return False
        else:
            vl = self.limit_question
            available_questions = self.env['question.bank'].search_count([
                ('category_group_ids', 'in', all_categories.ids)
            ])
            if available_questions < vl:
                raise ValidationError(
                    f"Số lượng câu hỏi không đủ. "
                    f"Cần {vl}, nhưng chỉ có {available_questions} câu hỏi."
                )
                return False
        return all_categories.ids

    def action_add_questions_by_category(self):
        all_categories = self.action_check_questions_availability()

        if not all_categories:
            return

        # Xóa các câu hỏi cũ
        old_questions = self.env['survey.question'].search([('survey_id', '=', self.id)])
        old_questions.unlink()

        # Tạo phân đoạn (dễ, trung bình, khó)
        self.questions_selection = 'random'
        self.access_mode = 'public'

        if self.bool_setting:
            if self.qty_de > 0:
                self.find_and_create_questions(all_categories, 'de', 'Câu hỏi dễ', self.qty_de)

            if self.qty_tb > 0:
                self.find_and_create_questions(all_categories, 'tb', 'Câu hỏi trung bình', self.qty_tb)

            if self.qty_kho > 0:
                self.find_and_create_questions(all_categories, 'kho', 'Câu hỏi khó', self.qty_kho)

        else:
            if self.limit_question > 0:
                self.find_and_create_questions(all_categories, None, 'Câu hỏi tổng hợp', self.limit_question)

        # Commit giao dịch
        self._cr.commit()
        return True

    def find_and_create_questions(self, category_ids, level, page_title, question_count):
        domain = [('category_group_ids', 'in', category_ids)]
        if self.bool_setting:
            domain.append(('level_question', '=', level))

        questions = self.env['question.bank'].search(domain)
        if questions:
            self.create_questions(questions, page_title, question_count)

    def create_questions(self, question_bank, page_title, random_questions_count):
        if question_bank:
            page = self.env['survey.question'].create({
                'title': page_title,
                'is_page': True,
                'survey_id': self.id,
                'random_questions_count': random_questions_count,
            })
            for question in question_bank:
                cau_hoi = self.env['survey.question'].create({
                    # 'background_image': question.background_image,
                    'title': question.title,
                    'description': question.description,
                    'question_type': question.question_type,
                    'survey_id': self.id,
                    'page_id': page.id,
                    'is_page': False,
                    'category_group_ids': [(6, 0, question.category_group_ids.ids)],
                    'level_question': question.level_question,
                })
                answer_ids = question.suggested_answer_ids.filtered(lambda r: r.value)
                answer_vals = answer_ids.mapped(lambda r: {
                    'question_id': cau_hoi.id,
                    'value': r.value,
                    'is_correct': r.is_correct,
                    'value_image': r.value_image,
                    'answer_score': 1 if r.is_correct else 0,
                })
                self.env['survey.question.answer'].sudo().create(answer_vals)


