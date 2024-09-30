# -*- coding: utf-8 -*-
{
    'name': 'Question Duplicator In Survey',
    'version': '17.0.1.0.0',
    'category': 'Marketing',
    'summary': """Option for duplicating survey questions.""",
    'description': """In this module, users can get an option for duplicating 
     questions for differnt survey.""",
    'author': 'Dao Duy Hung',
    'company': 'Viet Nam',
    'maintainer': 'Dao Duy Hung',
    'website': '',
    'depends': ['base','survey'],
    'data': [
        'security/ir.model.access.csv',
        'views/action_question_duplicate.xml',
        'wizards/question_duplicate_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
