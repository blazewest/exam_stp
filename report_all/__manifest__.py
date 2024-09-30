{
    'name': 'Report All',
    'version': '1.0',
    'summary': 'Module report dien bien',
    'category': 'Tools',
    'author': 'Duy Hung',
    'depends': ['base','survey_dienbien','report_py3o'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/survey_user_input_views.xml',
        'report/report_survey_user_input.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
