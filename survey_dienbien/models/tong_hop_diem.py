from odoo import api, fields, models

class TongHopDiem(models.Model):
    _name = 'tong.hop.diem'
    _description = 'tong.hop.diem'

    name = fields.Char(string='Tên phân loại')
    tong = fields.Integer(string='Tong', default=0)
    so_lieu1 = fields.Integer(string='Số liệu thực tế', default=0)
    so_lieu2 = fields.Float(string='Số liệu theo %', default=0)
    ghi_chu = fields.Char(string='Ghi chú xếp loại theo điểm')
    cuoc_thi = fields.Many2one('survey.survey',string='Cuộc thi')


