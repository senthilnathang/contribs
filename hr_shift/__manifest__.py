# -*- coding: utf-8 -*-
{
    'name': "Shift For Employees",
    'version': '1.0',
    'category': 'HR',
    'price': 10.00,
    'currency': 'EUR',
    'website': "https://www.twitter.com/senthilnathang",
    'license': 'OPL-1',
    'author': 'Senthilnathan G',
    'summary': 'Employee Shifts',
    'images': ['static/images/main_screenshot.png'],
    'depends': ['resource', 'hr', 'hr_payroll','portal'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_employee_shift_security.xml',
        'views/hr_employee_contract_view.xml',
    ],
    'installable': True,
    'application': True,
}
