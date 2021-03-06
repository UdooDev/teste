# -*- coding: utf-8 -*-

{
    'name': "Client Consigmnent",
    'summary': 'Odoo module for consignment control in client facitilies (example: a publisher controls his books in bookshops',
    'description': 'Odoo module for consignment control in client facitilies (example: a publisher controls his books in bookshops. It was designed for a publishing house.',
    'author': "Udoo",
    'website': "www.udoo.com.br",
    'category': 'General',
    'version': '12.0',
    'depends': ['base', 'purchase', 'stock', 'product'],

    'data': [
        'security/ir.model.access.csv',
        'views/email_template_purchase_consignment.xml',
        'views/consignment_view.xml',
        'views/purchase_view.xml',
        'views/res_view.xml'
    ],
    'application':True,
    # only loaded in demonstration mode
    #'demo': [
        # 'demo.xml',
    #],
}
