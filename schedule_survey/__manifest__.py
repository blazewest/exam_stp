{
    'name': 'Survey Scheduler',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'This module helps you schedule the survey, and the survey will'
               ' be automatically sent to the participants.',
    'description': "With the help of this module, the user can "
                   "schedule the survey and select the participants,"
                   "and the survey is automatically sent "
                   "to all selected participants.",
    'author': "Duy Hung",
    'company': '',
    'maintainer': 'Duy Hung',
    'website': "",
    'depends': ['base', 'survey'],
    'data': [
        'data/ir_cron_data.xml',
        'views/survey_survey_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
