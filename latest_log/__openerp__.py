{
    'name': 'Latest Log',
    'version': '1.0',
    'category': 'Others',
    'summary': 'Log latest models aand data viewed by user',
    'description': """
   This module will help you to see your latest data
    """,
    'author': 'Senthilnathan G',
    'website': 'http://www.twitter.com/senthilnathang',
    'depends': ['web'],
    'data': [
        'view/latest_log.xml',
        'security/ir.model.access.csv'
    ],
    'qweb': [
         'static/src/xml/template.xml'
    ],
     'images': ['images/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
}



