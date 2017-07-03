# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    'name': 'attivita',
    'version': '1.0',
    'author': 'Flosslab S.r.l',
    'sequence': 1,
    'category': 'Processi',
    'website': 'http://www.flosslab.com',
    'description': """
Gestione della attività
""",
    'css': [
        "static/src/css/style.css",
    ],
    'depends': [
        'base_setup',
        'board',
        'mail',
        'resource',
        'web_kanban',
        'hr',
    ],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'wizard/assegna_attivita_view.xml',
        'wizard/wizard_attivita_view.xml',
        'wizard/registra_aggiornamento_view.xml',
        'view/attivita_view.xml',
        'data/email_notifications.xml'
    ],
    'images': [],
    'update_xml': [],

    'demo': [],
    'application': True,
    'installable': True,
}
#
##############################################################################
