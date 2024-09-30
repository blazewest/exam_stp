from odoo import http
from odoo.http import request


class SurveyController(http.Controller):

    @http.route(['/check_score'], type='http', auth='public', website=True)
    def check_score(self, **kwargs):
        surveys = request.env['survey.survey'].sudo().search([])
        return request.render('survey_check_score.check_score_page', {'surveys': surveys})

    @http.route(['/check_score/result'], type='http', auth='public', website=True, csrf=False)
    def show_score(self, **post):
        survey_id = post.get('survey_id')
        partner_email = post.get('partner_email')
        partner = request.env['res.partner'].sudo().search([('email', '=', partner_email)], limit=1)
        survey = request.env['survey.user_input'].sudo().search(
            [('survey_id', '=', survey_id), ('partner_id', '=', partner.id)], limit=1)

        score = 0
        if survey:
            score = survey.scoring_total

        return request.render('survey_check_score.show_score_page', {'score': score, 'partner': partner})
