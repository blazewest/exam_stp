# -*- coding: utf-8 -*-
import logging
import werkzeug
from werkzeug.urls import url_encode

from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)

class CustomAuthSignupHome(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False, csrf=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        # Kiểm tra điều kiện token và signup_enabled
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                # Lấy thông tin từ form đăng ký
                qcontext['login'] = kw.get('login')
                qcontext['password'] = kw.get('password')
                qcontext['confirm_password'] = kw.get('confirm_password')
                qcontext['name'] = kw.get('name')
                qcontext['email'] = kw.get('email')
                qcontext['cccd'] = kw.get('cccd')
                qcontext['phone'] = kw.get('phone')
                qcontext['province'] = kw.get('province')
                qcontext['district'] = kw.get('district')
                qcontext['ward'] = kw.get('ward')
                qcontext['name_donvi_id'] = kw.get('name_donvi_id')

                # Thực hiện kiểm tra mật khẩu
                if qcontext['password'] != qcontext['confirm_password']:
                    qcontext['error'] = _("Mật khẩu không khớp, vui lòng nhập lại.")
                    return request.render('auth_signup.signup', qcontext)

                # Thực hiện hành động dưới quyền `sudo` để bỏ qua các giới hạn về quyền
                self.do_signup(qcontext)

                # Chuyển hướng đến trang đăng nhập sau khi đăng ký thành công
                return self.web_login(*args, **kw)

            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Đã có người dùng khác đăng ký bằng địa chỉ email này.")
                else:
                    _logger.warning("%s", e)
                    qcontext['error'] = _("Không thể tạo tài khoản mới.") + "\n" + str(e)

        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')), ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % url_encode({'login': user.login, 'redirect': '/web'}))

        # Render lại trang signup với context đã cập nhật
        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    def _prepare_signup_values(self, qcontext):
        values = {
            key: qcontext.get(key)
            for key in ('login', 'name', 'password', 'email', 'cccd', 'phone','name_donvi_id')
        }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Mật khẩu không khớp, vui lòng nhập lại."))

        # Lấy ngôn ngữ từ context nếu có
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang

        return values

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = self._prepare_signup_values(qcontext)
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

