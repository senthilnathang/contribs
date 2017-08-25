# -*- coding: utf-8 -*-

{
    'name': 'Virus Scanner using Virus Total',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 25,
    'summary': 'Virus Scanner for Attachments uploaded by applicants or any other webform',
    'description': """This module allows you to scan files""",
    'author': 'Senthilnathan G',
    'website': 'https://www.twitter.com/senthilnathang',
    'depends': [
        'hr_recruitment',
    ],
    'data': [
    #~ 'views/res_company_views.xml',
    ],
    'demo': [
    ],
    'images': [
    'images/main_screenshot.png',
    'images/main_screenshot1.png',
    'images/main_screenshot2.png',
    'images/main_screenshot3.png',
    ],
    'installable': True,
    'atcive': True,
    "external_dependencies": {
    'python': ['enum']
},
}
