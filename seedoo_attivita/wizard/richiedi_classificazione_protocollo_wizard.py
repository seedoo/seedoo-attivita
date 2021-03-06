# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import logging
from openerp.osv import fields, osv
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT as DSDF)
from openerp.tools.translate import _
import time
from openerp import netsvc
import datetime
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class wizard_classifica(osv.TransientModel):
    _inherit = 'protocollo.classifica.wizard'

    def action_save(self, cr, uid, ids, context=None):
        result = super(wizard_classifica, self).action_save(cr, uid, ids, context)
        self.pool.get('attivita.attivita').synchro_protocol_action(context, cr, uid, 'seedoo_protocollo', 'protocollo_classifica_action')
        return result


class wizard(osv.TransientModel):
    """
        Wizard per la richiesta di classificazione
    """
    _name = 'protocollo.classify.wizard'
    _description = 'Richiedi Classificazione Wizard'

    _columns = {
        'name': fields.text(
            'Note Richiesta',
            required=True,
            readonly=False
        ),
        'assegnatario': fields.many2one(
            'hr.employee','Assegnatario',
            required=True,
            readonly=False
        ),

    }

    def action_request(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        protocollo_id = context['active_id']
        protocollo_obj = self.pool.get('protocollo.protocollo')
        prot = protocollo_obj.browse(cr,uid,protocollo_id)

        now = datetime.datetime.now()
        categoria_obj = self.pool.get('attivita.categoria')
        category_ids = categoria_obj.search(cr,uid,[('name','=','Richiesta Classificazione Protocollo')])
        tempo_esecuzione_attivita = 15
        if len(category_ids) == 1:
            category = categoria_obj.browse(cr,uid,category_ids[0])
            tempo_esecuzione_attivita = category.tempo_standard
        data_scadenza =  now + datetime.timedelta(days=tempo_esecuzione_attivita)
        user = wizard.assegnatario.user_id

        activity_vals = {
            'name': "Richiesta Classificazione protocollo num %s a %s "%(prot.name,user.partner_id.name),
            'descrizione': wizard.name,
            'priorita': '3',
            'referente_id': prot.user_id.id,
            'assegnatario_id': user.id,
            'state': 'assegnato',
            'data_scadenza': data_scadenza,
            'data_assegnazione': now,
            'data_presa_carico': now,
            'categoria': category.id,
            'protocollo_id': prot.id
        }
        #TODO we need to use the uid instead of SUPERUSER_ID
        self.pool.get("attivita.attivita").create(cr,SUPERUSER_ID, activity_vals, context=None)
        return {'type': 'ir.actions.act_window_close'}
