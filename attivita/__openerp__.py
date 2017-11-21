# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

{
    "name": "Attività",
    "version": "8.0.1.6.0",
    "category": "Process",
    "summary": "Gestione Attività",
    "author": "Flosslab",
    "website": "http://www.flosslab.com",
    "license": "AGPL-3",
    "css": [
        "static/src/css/style.css",
    ],
    "depends": [
        "base_setup",
        "board",
        "mail",
        "resource",
        "web_kanban",
        "hr",
    ],
    "data": [
        "security/account_security.xml",
        "security/ir.model.access.csv",
        "wizard/assegna_attivita_view.xml",
        "wizard/wizard_attivita_view.xml",
        "wizard/registra_aggiornamento_view.xml",
        "view/attivita_view.xml",
        "data/email_notifications.xml"
    ],
    "application": True,
    "installable": True
}
