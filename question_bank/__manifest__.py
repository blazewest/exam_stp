{
    'name': 'Question bank',
    'version': '1.0',
    'summary': 'Module Survey Question bank dien bien',
    'category': 'Tools',
    'author': 'Duy Hung',
    'depends': ['base','survey_dienbien'],
    'data': [
        'security/ir.model.access.csv',
        'views/survey_question_views.xml',
        'views/survey_survey.xml'
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
