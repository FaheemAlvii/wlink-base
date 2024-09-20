{
    'name': 'WLink QR Whatsapp API Base',
    'author': 'WLink',
    'license': 'LGPL-3',
    'version': '16.0.1.0',
    'depends': ['mail'],
    'website':'https://wlink.geektechsol.com',
    'images': ['static/description/banner.png'],
    'description':'static/description/index.html',
    'data': [
        'security/ir.model.access.csv',
        'views/connections.xml',
        'wizard/login_menu.xml',

        'views/menu.xml'
    ],
    'installable': True,
}
