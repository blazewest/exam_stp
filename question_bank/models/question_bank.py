# -*- coding: utf-8 -*-
import collections
import contextlib
import itertools
import json
import operator
from textwrap import shorten

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError


class SurveyQuestion(models.Model):
    _name = 'question.bank'
    _description = 'Question Bank'
    _rec_name = 'title'
    _order = 'sequence,id'

    # question generic data
    level_question = fields.Selection([
        ('de', 'Dễ'),
        ('tb', 'Trung Bình'),
        ('kho', 'Khó')], string='Mức độ câu hỏi', default='de', required=True)
    category_group_ids = fields.Many2many('category.question', string='Lĩnh vực câu hỏi')
    title = fields.Char('Tiêu đề', required=True)
    description = fields.Html(
        'Mô tả',  sanitize=True, sanitize_overridable=True,
        help="Sử dụng trường này để thêm các giải thích bổ sung về câu hỏi của bạn hoặc để minh họa bằng hình ảnh hoặc video")
    question_placeholder = fields.Char("Trình giữ chỗ",  compute="_compute_question_placeholder", store=True, readonly=False)
    background_image = fields.Image("Background Image", readonly=False)
    sequence = fields.Integer('Trình tự', default=10)
    # page specific
    question_type = fields.Selection([
        ('simple_choice', 'Câu hỏi lựa chọn: một câu trả lời duy nhất'),
        ('multiple_choice', 'Câu hỏi lựa chọn: cho phép nhiều câu trả lời'),
        ('text_box', 'hộp văn bản'),
        ('char_box', 'Hộp văn bản 1 dòng'),
        ('numerical_box', 'Giá trị kiểu số'),
        ('date', 'Ngày'),
        ('datetime', 'Ngày giờ'),
        ('matrix', 'Ma trận')], string='Loại câu hỏi',
        compute='_compute_question_type', readonly=False, store=True)
    is_scored_question = fields.Boolean(
        'Ghi điểm', compute='_compute_is_scored_question',
        readonly=False, store=True, copy=True,
        help="Bao gồm câu hỏi này như một phần của việc chấm điểm bài kiểm tra. Cần phải có câu trả lời và điểm trả lời để được tính đến.")
    # -- scoreable/answerable simple answer_types: numerical_box / date / datetime
    answer_numerical_box = fields.Float('Câu trả lời đúng về số', help="Câu trả lời đúng cho câu hỏi này.")
    answer_date = fields.Date('Ngày trả lời đúng', help="Câu trả lời đúng cho câu hỏi này.")
    answer_datetime = fields.Datetime('Câu trả lời đúng về ngày giờ', help="Câu trả lời đúng ngày và giờ cho câu hỏi này.")
    # -- char_box
    validation_email = fields.Boolean('Dữ liệu phải là một email hợp lệ')
    save_as_email = fields.Boolean(
        "Lưu dưới dạng email người dùng", readonly=False, copy=True,
        help="Nếu được chọn, tùy chọn này sẽ lưu câu trả lời của người dùng dưới dạng địa chỉ email của họ.")
    save_as_nickname = fields.Boolean(
        "Lưu dưới dạng biệt danh người dùng", compute='_compute_save_as_nickname', readonly=False, store=True, copy=True,
        help="Nếu được chọn, tùy chọn này sẽ lưu câu trả lời của người dùng dưới dạng biệt danh.")
    # -- simple choice / multiple choice / matrix
    suggested_answer_ids = fields.One2many(
        'question.bank.answer', 'question_id', string='Các loại câu trả lời', copy=True,
        help='Nhãn được sử dụng cho các lựa chọn được đề xuất: lựa chọn đơn giản, lựa chọn nhiều và các cột ma trận')
    # -- matrix
    matrix_subtype = fields.Selection([
        ('simple', 'Một lựa chọn cho mỗi hàng'),
        ('multiple', 'Nhiều lựa chọn cho mỗi hàng')], string='Kiểu Ma trận', default='simple')
    matrix_row_ids = fields.One2many(
        'question.bank.answer', 'matrix_question_id', string='Hàng Ma trận', copy=True,
        help='Nhãn được sử dụng cho các lựa chọn được đề xuất: các hàng ma trận')
    # -- display & timing options
    # -- comments (simple choice, multiple choice, matrix (without count as an answer))
    # question validation
    # answers
    user_input_line_ids = fields.One2many(
        'survey.user_input.line', 'question_id', string='Câu trả lời',
        domain=[('skipped', '=', False)], groups='survey.group_survey_user')


    _sql_constraints = [
        ('scored_datetime_have_answers', "CHECK (is_scored_question != True OR question_type != 'datetime' OR answer_datetime is not null)",
            'All "Is a scored question = True" and "Question Type: Datetime" questions need an answer'),
        ('scored_date_have_answers', "CHECK (is_scored_question != True OR question_type != 'date' OR answer_date is not null)",
            'All "Is a scored question = True" and "Question Type: Date" questions need an answer'),
    ]

    @api.constrains('category_group_ids')
    def _check_category_group_hierarchy(self):
        for record in self:
            all_categories = record.category_group_ids
            all_category_ids = all_categories.ids

            for category in all_categories:
                # Lấy tất cả các danh mục cha và con của danh mục hiện tại
                parent = category.parent_id
                while parent:
                    if parent.id in all_category_ids:
                        raise ValidationError(
                            "Không thể chọn các danh mục có quan hệ cha-con: %s và %s" % (parent.name, category.name)
                        )
                    parent = parent.parent_id

                # Lấy tất cả các danh mục con của danh mục hiện tại
                children = category.child_ids
                while children:
                    if any(child.id in all_category_ids for child in children):
                        raise ValidationError(
                            "Không thể chọn các danh mục có quan hệ cha-con: %s và %s" % (
                            category.name, children.mapped('name'))
                        )
                    children = children.mapped('child_ids')

    @api.constrains('level_question', 'category_group_ids', 'title')
    def _check_unique_question(self):
        for record in self:
            # Tìm tất cả các bản ghi khác có cùng level_question, title, và category_group_ids
            existing_records = self.search([
                ('id', '!=', record.id),
                ('level_question', '=', record.level_question),
                ('title', '=', record.title),
                ('category_group_ids', 'in', record.category_group_ids.ids)
            ])

            if existing_records:
                raise ValidationError(
                    "Đã tồn tại một câu hỏi với mức độ, lĩnh vực và tiêu đề giống hệt."
                )
    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('question_type')
    def _compute_question_placeholder(self):
        for question in self:
            if question.question_type in ('simple_choice', 'multiple_choice', 'matrix') \
                    or not question.question_placeholder:  # avoid CacheMiss errors
                question.question_placeholder = False

    @api.depends('question_type')
    def _compute_save_as_nickname(self):
        for question in self:
            if question.question_type != 'char_box':
                question.save_as_nickname = False

    @api.depends('question_type', 'answer_date', 'answer_datetime', 'answer_numerical_box', 'suggested_answer_ids.is_correct')
    def _compute_is_scored_question(self):
        for question in self:
            if question.question_type == 'date':
                question.is_scored_question = bool(question.answer_date)
            elif question.question_type == 'datetime':
                question.is_scored_question = bool(question.answer_datetime)
            elif question.question_type == 'numerical_box' and question.answer_numerical_box:
                question.is_scored_question = True
            elif question.question_type in ['simple_choice', 'multiple_choice']:
                question.is_scored_question = any(question.suggested_answer_ids.mapped('is_correct'))
            else:
                question.is_scored_question = False


    # ------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------

    def validate_question(self, answer, comment=None):
        self.ensure_one()
        if isinstance(answer, str):
            answer = answer.strip()
        # Empty answer to mandatory question
        # because in choices question types, comment can count as answer
        else:
            if self.question_type == 'char_box':
                return self._validate_char_box(answer)
            elif self.question_type == 'numerical_box':
                return self._validate_numerical_box(answer)
            elif self.question_type in ['date', 'datetime']:
                return self._validate_date(answer)
            elif self.question_type in ['simple_choice', 'multiple_choice']:
                return self._validate_choice(answer, comment)
            elif self.question_type == 'matrix':
                return self._validate_matrix(answer)
        return {}


    def _index(self):
        self.ensure_one()
        return list(self.survey_id.question_and_page_ids).index(self)

    # ------------------------------------------------------------
    # STATISTICS / REPORTING
    # ------------------------------------------------------------

    def _prepare_statistics(self, user_input_lines):
        """ Compute statistical data for questions by counting number of vote per choice on basis of filter """
        all_questions_data = []
        for question in self:
            question_data = {'question': question}

            # fetch answer lines, separate comments from real answers
            all_lines = user_input_lines.filtered(lambda line: line.question_id == question)
            if question.question_type in ['simple_choice', 'multiple_choice', 'matrix']:
                answer_lines = all_lines.filtered(
                    lambda line: line.answer_type == 'suggestion' or (
                        line.skipped and not line.answer_type) or (
                        line.answer_type == 'char_box')
                    )
                comment_line_ids = all_lines.filtered(lambda line: line.answer_type == 'char_box')
            else:
                answer_lines = all_lines
                comment_line_ids = self.env['survey.user_input.line']
            skipped_lines = answer_lines.filtered(lambda line: line.skipped)
            done_lines = answer_lines - skipped_lines
            question_data.update(
                answer_line_ids=answer_lines,
                answer_line_done_ids=done_lines,
                answer_input_done_ids=done_lines.mapped('user_input_id'),
                answer_input_skipped_ids=skipped_lines.mapped('user_input_id'),
                comment_line_ids=comment_line_ids)
            question_data.update(question._get_stats_summary_data(answer_lines))

            # prepare table and graph data
            table_data, graph_data = question._get_stats_data(answer_lines)
            question_data['table_data'] = table_data
            question_data['graph_data'] = json.dumps(graph_data)

            all_questions_data.append(question_data)
        return all_questions_data

    def _get_stats_data(self, user_input_lines):
        if self.question_type == 'simple_choice':
            return self._get_stats_data_answers(user_input_lines)
        elif self.question_type == 'multiple_choice':
            table_data, graph_data = self._get_stats_data_answers(user_input_lines)
            return table_data, [{'key': self.title, 'values': graph_data}]
        elif self.question_type == 'matrix':
            return self._get_stats_graph_data_matrix(user_input_lines)
        return [line for line in user_input_lines], []

    def _get_stats_data_answers(self, user_input_lines):
        suggested_answers = [answer for answer in self.mapped('suggested_answer_ids')]

        count_data = dict.fromkeys(suggested_answers, 0)
        for line in user_input_lines:
            if line.suggested_answer_id in count_data\
               or (line.value_char_box):
                count_data[line.suggested_answer_id] += 1

        table_data = [{
            'value': 'Other (see comments)' if not sug_answer else sug_answer.value,
            'suggested_answer': sug_answer,
            'count': count_data[sug_answer]
            }
            for sug_answer in suggested_answers]
        graph_data = [{
            'text': 'Other (see comments)' if not sug_answer else sug_answer.value,
            'count': count_data[sug_answer]
            }
            for sug_answer in suggested_answers]

        return table_data, graph_data

    def _get_stats_graph_data_matrix(self, user_input_lines):
        suggested_answers = self.mapped('suggested_answer_ids')
        matrix_rows = self.mapped('matrix_row_ids')

        count_data = dict.fromkeys(itertools.product(matrix_rows, suggested_answers), 0)
        for line in user_input_lines:
            if line.matrix_row_id and line.suggested_answer_id:
                count_data[(line.matrix_row_id, line.suggested_answer_id)] += 1

        table_data = [{
            'row': row,
            'columns': [{
                'suggested_answer': sug_answer,
                'count': count_data[(row, sug_answer)]
            } for sug_answer in suggested_answers],
        } for row in matrix_rows]
        graph_data = [{
            'key': sug_answer.value,
            'values': [{
                'text': row.value,
                'count': count_data[(row, sug_answer)]
                }
                for row in matrix_rows
            ]
        } for sug_answer in suggested_answers]

        return table_data, graph_data

    def _get_stats_summary_data(self, user_input_lines):
        stats = {}
        if self.question_type in ['simple_choice', 'multiple_choice']:
            stats.update(self._get_stats_summary_data_choice(user_input_lines))
        elif self.question_type == 'numerical_box':
            stats.update(self._get_stats_summary_data_numerical(user_input_lines))

        if self.question_type in ['numerical_box', 'date', 'datetime']:
            stats.update(self._get_stats_summary_data_scored(user_input_lines))
        return stats

    def _get_stats_summary_data_choice(self, user_input_lines):
        right_inputs, partial_inputs = self.env['survey.user_input'], self.env['survey.user_input']
        right_answers = self.suggested_answer_ids.filtered(lambda label: label.is_correct)
        if self.question_type == 'multiple_choice':
            for user_input, lines in tools.groupby(user_input_lines, operator.itemgetter('user_input_id')):
                user_input_answers = self.env['survey.user_input.line'].concat(*lines).filtered(lambda l: l.answer_is_correct).mapped('suggested_answer_id')
                if user_input_answers and user_input_answers < right_answers:
                    partial_inputs += user_input
                elif user_input_answers:
                    right_inputs += user_input
        else:
            right_inputs = user_input_lines.filtered(lambda line: line.answer_is_correct).mapped('user_input_id')
        return {
            'right_answers': right_answers,
            'right_inputs_count': len(right_inputs),
            'partial_inputs_count': len(partial_inputs),
        }

    def _get_stats_summary_data_numerical(self, user_input_lines):
        all_values = user_input_lines.filtered(lambda line: not line.skipped).mapped('value_numerical_box')
        lines_sum = sum(all_values)
        return {
            'numerical_max': max(all_values, default=0),
            'numerical_min': min(all_values, default=0),
            'numerical_average': round(lines_sum / (len(all_values) or 1), 2),
        }

    def _get_stats_summary_data_scored(self, user_input_lines):
        return {
            'common_lines': collections.Counter(
                user_input_lines.filtered(lambda line: not line.skipped).mapped('value_%s' % self.question_type)
            ).most_common(5),
            'right_inputs_count': len(user_input_lines.filtered(lambda line: line.answer_is_correct).mapped('user_input_id'))
        }

    # ------------------------------------------------------------
    # OTHERS
    # ------------------------------------------------------------

    def _get_correct_answers(self):
        correct_answers = {}

        # Simple and multiple choice
        choices_questions = self.filtered(lambda q: q.question_type in ['simple_choice', 'multiple_choice'])
        if choices_questions:
            suggested_answers_data = self.env['question.bank.answer'].search_read(
                [('question_id', 'in', choices_questions.ids), ('is_correct', '=', True)],
                ['question_id', 'id'],
                load='', # prevent computing display_names
            )
            for data in suggested_answers_data:
                if not data.get('id'):
                    continue
                correct_answers.setdefault(data['question_id'], []).append(data['id'])

        # Numerical box, date, datetime
        for question in self - choices_questions:
            if question.question_type not in ['numerical_box', 'date', 'datetime']:
                continue
            answer = question[f'answer_{question.question_type}']
            if question.question_type == 'date':
                answer = tools.format_date(self.env, answer)
            elif question.question_type == 'datetime':
                answer = tools.format_datetime(self.env, answer, tz='UTC', dt_format=False)
            correct_answers[question.id] = answer

        return correct_answers

class SurveyQuestionAnswer(models.Model):
    _name = 'question.bank.answer'
    _rec_name = 'value'
    _rec_names_search = ['question_id.title', 'value']
    _order = 'question_id, sequence, id'
    _description = 'Survey Label'

    MAX_ANSWER_NAME_LENGTH = 90  # empirically tested in client dropdown

    # question and question related fields
    question_id = fields.Many2one('question.bank', string='Câu hỏi', ondelete='cascade', index='btree_not_null')
    matrix_question_id = fields.Many2one('question.bank', string='Câu hỏi (dưới dạng hàng ma trận)', ondelete='cascade', index='btree_not_null')
    question_type = fields.Selection(related='question_id.question_type')
    sequence = fields.Integer('Thứ tự ưu tiên nhãn dán', default=10)
    # answer related fields
    value = fields.Char('Giá trị được gợi ý', required=True)
    value_image = fields.Image('Hình ảnh', max_width=1024, max_height=1024)
    value_image_filename = fields.Char('Tên tệp hình ảnh')
    is_correct = fields.Boolean('Chính xác')

    @api.depends('value', 'question_id.question_type', 'question_id.title', 'matrix_question_id')
    def _compute_display_name(self):
        for answer in self:
            if not answer.question_id or answer.question_id.question_type == 'matrix':
                answer.display_name = answer.value
                continue
            title = answer.question_id.title or "[Question Title]"
            n_extra_characters = len(title) + len(answer.value) + 3 - self.MAX_ANSWER_NAME_LENGTH  # 3 for `" : "`
            if n_extra_characters <= 0:
                answer.display_name = f'{title} : {answer.value}'
            else:
                answer.display_name = shorten(
                    f'{shorten(title, max(30, len(title) - n_extra_characters), placeholder="...")} : {answer.value}',
                    self.MAX_ANSWER_NAME_LENGTH,
                    placeholder="..."
                )

    @api.constrains('question_id', 'matrix_question_id')
    def _check_question_not_empty(self):
        for label in self:
            if not bool(label.question_id) != bool(label.matrix_question_id):
                raise ValidationError("Mỗi câu hỏi chỉ được gắn nhãn.")

    def _get_answer_matching_domain(self, row_id=False):
        self.ensure_one()
        if self.question_type == "matrix":
            return ['&', '&', ('question_id', '=', self.question_id.id), ('matrix_row_id', '=', row_id), ('suggested_answer_id', '=', self.id)]
        elif self.question_type in ('multiple_choice', 'simple_choice'):
            return ['&', ('question_id', '=', self.question_id.id), ('suggested_answer_id', '=', self.id)]
        return []
