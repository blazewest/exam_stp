{
    'name': 'custumal user',
    'version': '1.0',
    'summary': 'Module custumal user dien bien',
    'category': 'Tools',
    'author': 'Duy Hung',
    'depends': ['base','survey_dienbien'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/survey_question_views.xml',
        'views/re_users_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
