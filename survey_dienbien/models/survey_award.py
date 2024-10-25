from odoo import api, fields, models, _
from datetime import datetime

class SurveyAward(models.Model):
    _name = 'survey.award'
    _description = 'Survey Award Calculation'

    survey_id = fields.Many2one('survey.survey', string='Cuộc thi', required=True, ondelete='cascade')
    sum_partner = fields.Integer(string='Tổng số người thi', compute='_compute_sum_partner', store=True)
    sum_exam = fields.Integer(string='Tổng số bài thi', compute='_compute_sum_exam', store=True)
    list_don_vi = fields.One2many('survey.award.donvi', 'survey_award_id', string='Những đơn vị đã tham gia')
    scheduled_date = fields.Datetime(related='survey_id.scheduled_date', string='Ngày thi', store=True)
    archived_date = fields.Datetime(related='survey_id.archived_date', string='Ngày kết thúc', store=True)
    time_limit = fields.Float(related='survey_id.time_limit', string='Thời gian thi (phút)', store=True)
    award_result_ids = fields.One2many('survey.award.result', 'survey_award_id', string='Xếp loại')
    award_ids = fields.One2many(related='survey_id.award_ids', string='Giải thưởng', readonly=True)

    @api.depends('survey_id','survey_id.active')
    def _compute_sum_partner(self):
        """Tính tổng số người tham gia (không tính trùng lặp) chỉ khi cuộc thi đã kết thúc."""
        for record in self:
            if record.archived_date and record.archived_date <= fields.Datetime.now():
                # Đếm số lượng partner_id không trùng lặp trong 'survey.user_input'
                record.sum_partner = len(set(self.env['survey.user_input'].search([
                    ('survey_id', '=', record.survey_id.id),
                    ('test_entry', '=', False)
                ]).mapped('partner_id')))
            else:
                record.sum_partner = 0

    @api.depends('survey_id','survey_id.active')
    def _compute_sum_exam(self):
        """Tính tổng số bài thi (không bao gồm bài thi test_entry=True) chỉ khi cuộc thi đã kết thúc."""
        for record in self:
            if record.archived_date and record.archived_date <= fields.Datetime.now():
                # Đếm tổng số bài thi với test_entry=False
                record.sum_exam = self.env['survey.user_input'].search_count([
                    ('survey_id', '=', record.survey_id.id),
                    ('test_entry', '=', False)
                ])
            else:
                record.sum_exam = 0

    @api.depends('survey_id','survey_id.active')
    def _compute_list_don_vi(self):
        """Tính danh sách các đơn vị tham gia, không trùng lặp chỉ khi cuộc thi đã kết thúc."""
        for record in self:
            if record.archived_date and record.archived_date <= fields.Datetime.now():
                # Lấy tất cả các partner_id và res.partner.name_donvi_id (đơn vị của đối tác)
                partners = self.env['survey.user_input'].search([
                    ('survey_id', '=', record.survey_id.id),
                    ('test_entry', '=', False)
                ]).mapped('partner_id')

                # Lấy danh sách các đơn vị tham gia, không trùng lặp
                don_vi_ids = list(set(partners.mapped('name_donvi_id')))
                record.list_don_vi = [(6, 0, [don_vi.id for don_vi in don_vi_ids])]
            else:
                record.list_don_vi = [(5, 0, 0)]  # Clear the list if the survey hasn't ended

    def calculate_awards(self):
        """Hàm tính toán xếp loại khi nhấn nút"""
        for record in self:
            # Xóa các kết quả xếp loại cũ
            record.award_result_ids.unlink()

            # Khôi phục số lượng giải thưởng còn lại về giá trị ban đầu
            for award in record.award_ids:
                award.write({'remaining_qty_award': award.qty_award})

            # Lấy tất cả các bài thi (survey.user_input) của cuộc thi
            user_inputs = self.env['survey.user_input'].search(
                [('survey_id', '=', record.survey_id.id), ('test_entry', '=', False)])

            if not user_inputs:
                continue  # Không có bài thi nào, bỏ qua cuộc thi này

            # Lấy tất cả các giải thưởng từ cuộc thi
            awards = record.award_ids.sorted(key=lambda a: a.priority_level)

            if not awards:
                continue  # Không có giải thưởng nào, bỏ qua

            # Sắp xếp các bài thi dựa trên các tiêu chí đã nêu
            sorted_user_inputs = sorted(user_inputs, key=lambda r: (
                -r.scoring_percentage,  # Điểm số từ cao xuống thấp
                abs(r.input_important - record.sum_partner),  # Gần nhất với tổng số người tham gia (sum_partner)
                r.end_datetime or fields.Datetime.now()  # Thời gian nộp sớm nhất
            ))

            # Phân bổ giải thưởng dựa trên các bài thi đã sắp xếp
            partner_award_count = {}  # Theo dõi số lượng giải mà mỗi partner đã nhận
            for award in awards:
                available_qty = award.remaining_qty_award

                if available_qty <= 0:
                    continue  # Nếu giải thưởng đã hết, bỏ qua

                for user_input in sorted_user_inputs:
                    partner_id = user_input.partner_id.id

                    # Giới hạn mỗi người nhận tối đa 1 giải thưởng
                    if partner_award_count.get(partner_id, 0) >= 1:
                        continue  # Người này đã nhận đủ 1 giải thưởng, bỏ qua

                    if available_qty <= 0:
                        break  # Không còn giải thưởng nào

                    # Tạo bản ghi xếp loại cho bài thi
                    self.env['survey.award.result'].create({
                        'survey_award_id': record.id,
                        'user_input_id': user_input.id,
                        'prize': dict(self.env['award'].fields_get(allfields=['name'])['name']['selection'])[
                            award.name],
                    })

                    # Cập nhật số lượng giải thưởng mà người này đã nhận
                    partner_award_count[partner_id] = partner_award_count.get(partner_id, 0) + 1

                    # Giảm số lượng giải thưởng còn lại
                    available_qty -= 1
                    award.write({'remaining_qty_award': available_qty})


class SurveyAwardResult(models.Model):
    _name = 'survey.award.result'
    _description = 'Survey Award Result'

    survey_award_id = fields.Many2one('survey.award', string='Survey Award', required=True, ondelete='cascade')

    user_input_id = fields.Many2one('survey.user_input', string='Bài thi', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Người thi', related='user_input_id.partner_id', store=True)
    name = fields.Char(string='Tên người tham gia', related='user_input_id.partner_id.name', store=True)
    scoring_percentage = fields.Float(string='Điểm số', related='user_input_id.scoring_percentage', store=True)
    prize = fields.Char(string='Giải thưởng', store=True)
    input_important = fields.Float(string='Dự đoán', related='user_input_id.input_important', store=True)
    xep_loai = fields.Char(string='Xếp loai',related='user_input_id.xep_loai', store=True)
    end_datetime = fields.Datetime('Thời gian nộp bài', readonly=True,related='user_input_id.end_datetime', store=True)

class SurveyAwardDonVi(models.Model):
    _name = 'survey.award.donvi'
    _description = 'Survey Award DonVi Information'

    survey_award_id = fields.Many2one('survey.award', string='Survey Award', required=True, ondelete='cascade')
    name = fields.Many2one('donvi', string='Tên Đơn Vị', required=True)
    total_exams = fields.Integer(string='Tổng số bài thi', compute='_compute_total_exams', store=True)
    total_participants = fields.Integer(string='Tổng số người thi', compute='_compute_total_participants', store=True)

    @api.depends('survey_award_id')
    def _compute_total_exams(self):
        """Tính tổng số bài thi của đơn vị này."""
        for record in self:
            # Lấy các bài thi của đơn vị này từ survey.user_input
            exams = self.env['survey.user_input'].search([
                ('survey_id', '=', record.survey_award_id.survey_id.id),
                ('partner_id.name_donvi_id', '=', record.name.id),
                ('test_entry', '=', False)
            ])
            record.total_exams = len(exams)

    @api.depends('survey_award_id')
    def _compute_total_participants(self):
        """Tính tổng số người tham gia từ đơn vị này (không tính trùng lặp)."""
        for record in self:
            # Lấy các participant_id không trùng lặp từ survey.user_input
            participants = self.env['survey.user_input'].search([
                ('survey_id', '=', record.survey_award_id.survey_id.id),
                ('partner_id.name_donvi_id', '=', record.name.id),
                ('test_entry', '=', False)
            ]).mapped('partner_id')
            record.total_participants = len(set(participants))