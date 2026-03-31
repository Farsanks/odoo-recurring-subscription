# -*- coding: utf-8 -*-
{
    'name': "recurring_subscription",
    'application': True,
    'summary': "Recurring Subscription",
    'description': "Manage recurring subscriptions",
    'version': '1.0',
    'author': "Farsan",
    'website': 'https://www.farsan.com/',
    'category': 'Subscription',

    'depends': ['base', 'product','mail','contacts','crm','account','base_automation'],

    'data': [
        'data/sequence_data.xml',
        'data/cron_data.xml',
        'data/automated_action_data.xml',
        'security/ir.model.access.csv',
        'views/recurring_subscription_views.xml',
        'views/recurring_subscription_credit_views.xml',
        'views/billing_schedule_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/menus.xml',
    ],

    'installable': True,
    'auto_install': False,
    'sequence': 1,
}
