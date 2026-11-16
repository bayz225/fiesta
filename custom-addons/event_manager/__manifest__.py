{
    'name': "event_manager",
    'summary': "App pour gérer les événements",

    'description': """
        Module pour gérer les événement et invitation entre différent contact
    """,

    'author': "Bayz225",
    'website': "https://www.bayz225.ci",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '19.0.1',
    'sequence': -100,

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'mail', 'web',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/event_security.xml',
        'wizard/add_event_view.xml',
        'wizard/add_contact_to_event_view.xml',
        'wizard/add_guest_info_event_view.xml',
        'views/event_view.xml',
        'views/contacted_event_view.xml',
        'views/contact_view.xml',
        'views/res_partner_views.xml',
        'views/res_partner_dashboard_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [ 
            'event_manager/static/src/scss/soft-ui-dashboard.scss',
            'event_manager/static/src/js/dashboard.js', 
            'event_manager/static/src/xml/dashboard.xml', 
        ], 
    },
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'demo': [
        'demo/demo.xml',
    ],
    "license": "LGPL-3"
}

