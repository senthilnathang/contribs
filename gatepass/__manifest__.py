# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Gate Pass',
    'version' : '1.1',
    'summary': """Gate pass integrated with Inventory""",
    'description': 'This module adds gate pass feature integrated with inventory module.',
    'category': 'Inventory',
    'author': 'Senthilnathan G',
    'depends': ['base','stock'],
    'data': [
        "views/gatepass_views.xml",
        "security/ir.model.access.csv",
        "report/gatepass_report_config.xml",
        "report/gatepass_report_views.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
