# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{ 'name': 'Seedoo Attività',
    'version': '8.0.0.0.0',
    'category': 'Process',
    'summary': 'Gestione Attività Seedoo',
    'author': 'Flosslab',
    'website': 'http://www.flosslab.com.',
    'license': 'AGPL-3',
    "depends": [
        'seedoo_protocollo', 'attivita', 'seedoo_gedoc'
    ],
    "data": [
        'wizard/richiedi_classificazione_protocollo_wizard_view.xml',
        'wizard/richiedi_annullamento_protocollo_wizard_view.xml',
        'wizard/richiedi_protocollazione_wizard_view.xml',
        'wizard/richiedi_fascicolazione_protocollo_wizard_view.xml',
        'wizard/crea_attivita_protocollo_wizard_view.xml',
        'view/seedoo_attivita_view.xml',
        'view/gedoc_view.xml',
        'data/seedoo_attivita_data.xml',
        'security/ir.model.access.csv',
    ],
    "js": [],
    "css": [],
    "qweb": [],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
