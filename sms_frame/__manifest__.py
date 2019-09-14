{
    'name': "SMS Framework",
    'version': "1.0.6",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary':'Allows you to send and receive smses from multiple gateways',
    'description':'Allows you to send and receive smses from multiple gateways',    
    'license':'LGPL-3',
    'data': [
        'data/ir.cron.xml',
        'data/ir.model.access.csv',
        'data/sms.gateway.csv',
        'data/mail.message.subtype.csv',
        'views/sms_views.xml',
        'views/res_partner_views.xml',
        'views/sms_message_views.xml',
        'views/sms_template_views.xml',
        'views/sms_account_views.xml',
        'views/sms_number_views.xml',
        'views/sms_compose_views.xml',
        'views/ir_actions_server_views.xml',
        'views/ir_actions_todo.xml',
        'security/ir.model.access.csv',
    ],
    'depends': ['mail','base_automation'],
    'images':[
        'static/description/3.jpg',
    ],
    'qweb': ['static/src/xml/sms_compose.xml'],
    'installable': True,
}