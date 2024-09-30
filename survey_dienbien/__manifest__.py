{
    'name': 'Survey dien bien',
    'version': '1.0',
    'summary': 'Module Survey dien bien',
    'category': 'Tools',
    'author': 'Duy Hung',
    'depends': ['base','schedule_survey','schedule_survey'],
    'data': [
        'security/ir.model.access.csv',
        'views/category_question_views.xml',
        'views/survey_question_views.xml',
        'views/survey_survey.xml',
        'views/res_partner.xml',
        'views/survey_templates.xml',
        'views/survey_user_input_views.xml',
        'views/template_survey.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/survey_dienbien/static/src/css/custom_survey_styles.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
