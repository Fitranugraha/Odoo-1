# -*- coding: utf-8 -*-
{
    'name': "Website Business Directory",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary': "A directory of local companies",
    'license':'LGPL-3',
    'data': [
        'views/website_business_directory_templates.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_directory_department_views.xml',
        'views/website_directory_category_views.xml',
        'views/website_directory_level_views.xml',
        'views/website_directory_billingplan_views.xml',
        'views/res_country_state_city_import_views.xml',
        'views/res_country_state_city_views.xml',
        'views/website_directory_template_views.xml',
        'views/menus.xml',
        'data/website.menu.csv',
        'data/res.groups.csv',
        'data/website.directory.level.csv',
        'data/res.users.directory.level.xml',
        'data/website.page.csv',
        'templates/default/website.directory.template.csv',
        'templates/default/website.directory.template.page.csv',
        'templates/individual/templates.xml',
        'templates/individual/website.directory.template.csv',
        'templates/individual/website.directory.template.page.csv',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['mail','website'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}