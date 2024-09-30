# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SurveySurvey(models.Model):
    """Inherited this model for adding schedule operation"""
    _inherit = 'survey.survey'

    is_cron = fields.Boolean(string='Bật Cron', default=True,
                             help='Bật hành động cron để lập lịch khảo sát')
    scheduled_date = fields.Datetime(string='Ngày thực hiện', help='Chọn ngày lên lịch cho khảo sát này')
    archived_date = fields.Datetime(string='Ngày tự động lưu trữ', help='Chọn ngày lên lịch cho khảo sát này kết thúc')
    cron_status = fields.Selection([
        ('done', 'Done'),
        ('in_progress', 'In Progress'),
        ('clone', 'Clone')],
        help='Status of this survey', string='Trạng thái Cron',  readonly=True,copy= False)
    contact_ids = fields.Many2many('res.partner',string='Danh bạ hiện có',help='Choose or create the participants')
    cron_id = fields.Many2one('ir.cron', string='Cron Job', readonly=True, ondelete='set null')

    # Ràng buộc để kiểm tra archived_date > scheduled_date
    @api.constrains('archived_date', 'scheduled_date')
    def _check_dates(self):
        for record in self:
            if record.archived_date <= record.scheduled_date:
                raise ValidationError("Ngày lưu trữ tự động phải lớn hơn ngày thực hiện khảo sát.")


    @api.onchange('scheduled_date')
    def _onchange_scheduled_date(self):
        """Status of the schedule action"""
        if self.scheduled_date and self.scheduled_date >= fields.datetime.today():
            self.write({'cron_status': 'in_progress'})

    def send_scheduled_survey(self):
        """Email sending schedule action"""
        # Find surveys that are scheduled for today
        # and have not been processed yet
        surveys = self.env['survey.survey'].search(
            [('is_cron', '=', True),
             ('scheduled_date', '=', fields.datetime.today()),
             ('cron_status', '!=', 'done')])
        for survey in surveys:
            # Get the email template for inviting
            # users to participate in the survey
            template = self.env.ref('survey.mail_template_user_input_invite')
            # Prepare the local context for creating the survey invites
            local_context = dict(
                self.env.context,
                default_survey_id=survey.id,
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                notif_layout='mail.mail_notification_light',
            )
            # Create survey invites for each contact
            record = self.env["survey.invite"].sudo().with_context(
                local_context).create(
                {'partner_ids': [(4, i)
                                 for i in survey.mapped('contact_ids').ids]})
            record.action_invite()
            survey.sudo().write({
                'cron_status': 'done'
            })

    @api.model_create_multi
    def create(self, vals_list):
        # Tạo các bản ghi dựa trên danh sách các giá trị
        records = super(SurveySurvey, self).create(vals_list)

        # Xử lý từng bản ghi sau khi tạo
        for record, vals in zip(records, vals_list):
            if vals.get('archived_date') and record.is_cron:
                cron = self._create_cron_job(record)
                record.cron_id = cron.id

        return records

    def write(self, vals):
        res = super(SurveySurvey, self).write(vals)
        if 'archived_date' in vals and self.is_cron:
            for record in self:
                if record.cron_id:
                    # Cập nhật cron nếu đã có
                    record.cron_id.write({
                        'nextcall': vals['archived_date'],
                    })
                else:
                    # Tạo cron mới nếu chưa có
                    cron = self._create_cron_job(record)
                    record.cron_id = cron.id
        return res

    def _create_cron_job(self, record):
        """Tạo Cron Job cho survey"""
        cron_env = self.env['ir.cron']
        cron_name = f'Survey Archiving for {record.title}'
        cron = cron_env.create({
            'name': cron_name,
            'model_id': self.env.ref('survey.model_survey_survey').id,  # ID của mô hình survey.survey
            'state': 'code',
            'code': f"model.browse({record.id})._archive_survey()",
            'nextcall': record.archived_date,
            'numbercall': 1,  # Chỉ chạy một lần
            'interval_number': 1,
            'interval_type': 'days',  # Thời gian không quan trọng do chỉ chạy 1 lần
            'doall': True,
        })
        return cron

    def _archive_survey(self):
        """Phương thức chạy khi cron được kích hoạt"""
        self.write({'active': False})
        self.cron_status = 'done'

    @api.model
    def unlink(self):
        for record in self:
            if record.cron_id:
                record.cron_id.unlink()  # Xóa cron tương ứng
        return super(SurveySurvey, self).unlink()

