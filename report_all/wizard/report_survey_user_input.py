from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class PurchaseReport(models.TransientModel):
    _name = "report.survey.user_input"
    _description = 'Report survey.user_input'
    
    name = fields.Char(string='Name',required=False)
    sort = fields.Selection(
        string='Sort',
        selection=[('dien_max', 'Điểm từ cao đến thấp'),
                   ('diem_min', 'Điểm từ thấp đến cao'),
                   ('name_A', 'Tên từ A-->Z'),
                   ('name_z', 'Tên từ Z-->A'),],
        required=True, )
    time_limit = fields.Float(string='Time_limit', required=False)
    date = fields.Date(string='Date', required=False)
    don_vi = fields.Char(string='Don_vi', required=False)
    sum_partner = fields.Integer(string='Sum_partner', required=False)
    sum_survey = fields.Integer(string='Sum_survey', required=False)
    records_survey_user_input =fields.Many2many(comodel_name='survey.user_input', string='records_survey_user_input')
    name_survey = fields.Many2one('survey.survey', string='Tên Cuộc thi', required=True)

    # lay ban ghi khong trung partner_id
    def get_unique_partner_survey_user_input(self):
        # Xác định thứ tự sắp xếp dựa trên self.sort
        order = ''
        if self.sort == 'dien_max':
            order = 'scoring_total desc'
        elif self.sort == 'dien_min':
            order = 'scoring_total asc'
        elif self.sort == 'name_A':
            order = 'partner_name_clean asc'
        elif self.sort == 'name_z':
            order = 'partner_name_clean desc'

        # Tìm kiếm tất cả các bản ghi survey.user_input theo survey_id và sắp xếp dựa trên thứ tự
        records_survey_user_input = self.env['survey.user_input'].search(
            [('survey_id', '=', self.name_survey.id)], order=order
        )

        # Khởi tạo dictionary để lưu các partner_id đã gặp
        unique_partners = {}

        # Lọc các bản ghi theo partner_id, chỉ giữ lại 1 bản ghi cho mỗi partner_id
        unique_records = self.env['survey.user_input']
        for record in records_survey_user_input:
            if record.partner_id.id not in unique_partners:
                unique_partners[record.partner_id.id] = record
                unique_records |= record

        return unique_records

    def create_report_survey_user_input(self):
        # Lấy thông tin từ name_survey
        self.time_limit = self.name_survey.time_limit
        self.date = self.name_survey.scheduled_date

        # Lấy các bản ghi không trùng lặp partner_id

        records_survey_user_input = self.get_unique_partner_survey_user_input()
        self.records_survey_user_input = records_survey_user_input
        # Tổng số bản ghi partner_id
        self.sum_partner = len(records_survey_user_input)

        don_vi_list = list(
            set(record.partner_id.name_donvi for record in records_survey_user_input if record.partner_id.name_donvi))
        if don_vi_list:
            self.don_vi = ', '.join(don_vi_list)
        else:
            self.don_vi = ''

        # Tính tổng của trường so_lan_lam từ các bản ghi records_survey_user_input
        self.sum_survey = sum(record.so_lan_lam for record in records_survey_user_input)


        action = self.env.ref('report_all.report_survey_user_input_py3o').report_action(self.id)
        return action

