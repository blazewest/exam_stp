
from odoo import api, fields, models, tools
from odoo.exceptions import ValidationError

province_codes = [
        '001', '002', '004', '006', '008', '010', '011', '012', '014', '015',
        '017', '019', '020', '022', '024', '025', '026', '027', '030', '031',
        '033', '034', '035', '036', '037', '038', '040', '042', '044', '045',
        '046', '048', '049', '051', '052', '054', '056', '058', '060', '062',
        '064', '066', '067', '068', '070', '072', '074', '075', '077', '079',
        '080', '082', '083', '084', '086', '087', '089', '091', '092', '093',
        '094', '095', '096'
    ]

class Partner(models.Model):
    _inherit = "res.partner"

    name_donvi_id = fields.Many2one('donvi', string='Tên Đơn Vị', required=False)
    cccd = fields.Char(string='Số Cccd', required=False)
    tai_khoan = fields.Char(string='Tên tài khoản', required=False)

    @api.constrains('cccd')
    def _check_cccd(self):
        for record in self:
            cccd = record.cccd
            if cccd:
                # Kiểm tra độ dài phải là 12 ký tự
                if len(cccd) != 12:
                    raise ValidationError("CCCD phải có đúng 12 chữ số.")

                # Kiểm tra 3 chữ số đầu tiên là mã tỉnh
                province_code = cccd[:3]
                if province_code not in province_codes:
                    raise ValidationError("3 chữ số đầu tiên của CCCD phải là mã tỉnh hợp lệ.")

                # Kiểm tra mã giới tính và mã năm sinh
                gender_code = cccd[3]
                birth_year_code = cccd[4:6]
                if not (gender_code.isdigit() and birth_year_code.isdigit()):
                    raise ValidationError(
                        "Ký tự thứ 4 phải là số (mã giới tính), ký tự thứ 5 và 6 phải là số (mã năm sinh).")

                # Kiểm tra mã giới tính và thế kỷ
                gender_code = int(gender_code)
                birth_year = int(birth_year_code)
                if (gender_code in [0, 1] and 0 <= birth_year <= 99):
                    # Thế kỷ 20 (1900-1999): Nam 0, nữ 1
                    pass
                elif (gender_code in [2, 3] and 0 <= birth_year <= 99):
                    # Thế kỷ 21 (2000-2099): Nam 2, nữ 3
                    pass
                elif (gender_code in [4, 5] and 0 <= birth_year <= 99):
                    # Thế kỷ 22 (2100-2199): Nam 4, nữ 5
                    pass
                elif (gender_code in [6, 7] and 0 <= birth_year <= 99):
                    # Thế kỷ 23 (2200-2299): Nam 6, nữ 7
                    pass
                elif (gender_code in [8, 9] and 0 <= birth_year <= 99):
                    # Thế kỷ 24 (2300-2399): Nam 8, nữ 9
                    pass
                else:
                    raise ValidationError("Mã giới tính và mã năm sinh không hợp lệ.")

                # Kiểm tra 6 chữ số cuối là số ngẫu nhiên
                random_digits = cccd[6:]
                if not random_digits.isdigit():
                    raise ValidationError("6 chữ số cuối của CCCD phải là số ngẫu nhiên.")
