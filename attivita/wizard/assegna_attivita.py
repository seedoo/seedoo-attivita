# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
import time
from openerp.tools.translate import _


class assegna_attivita(osv.osv_memory):
    _name = 'attivita.assegna.attivita'
    _description = 'Assegnazione Attivita'

    _columns = {
        'assegnatario_id': fields.many2one('res.users', 'Assegnatario',
                                           required=True,
                                           domain="[('is_visible','=',True)]"),
        'notifica': fields.boolean('Notifica'),
        'data_scadenza': fields.date('Data Scadenza', required=True),
        'presa_carico_libera': fields.boolean('Assegnazione Pubblica'),

    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(assegna_attivita, self).default_get(cr, uid, fields,
                                                        context=context)
        if 'active_id' in context.keys():
            attivita_obj = self.pool.get('attivita.attivita')
            attivita = attivita_obj.browse(cr, uid, context['active_id'])
            if attivita:
                res['data_scadenza'] = attivita.data_scadenza
        return res

    def assegna(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        attivita_obj = self.pool.get('attivita.attivita')
        attivita_id = context and context.get('active_id') or False
        for this in self.browse(cr, uid, ids, context=context):
            context['assegnazione'] = True
            attivita = attivita_obj.browse(cr, uid, attivita_id)
            if attivita.state == 'assegnato' and attivita.assegnatario_id.id != uid:
                raise osv.except_osv(_('Attenzione!'), _(
                    "Solo l'assegnatario puo' smistare l'attivita'!"))
            attivita_obj.write(cr, uid, attivita_id, {'state': 'assegnato',
                                                      'data_assegnazione': time.strftime(
                                                          "%Y-%m-%d"),
                                                      'data_scadenza': this.data_scadenza,
                                                      'assegnatario_id': this.assegnatario_id.id})
            # Gestione della notifica

            template_model_data = self.pool.get('ir.model.data').search(cr,
                                                                        uid, [(
                    'name',
                    '=',
                    'template_email_notifica_assegnatario_assegnazione')])
            if len(template_model_data):
                if isinstance(ids, list):
                    ids = ids[0]
                template_id = self.pool.get('ir.model.data').browse(cr, uid,
                                                                    template_model_data[
                                                                        0])
                self.pool.get('email.template').generate_email(cr, uid,
                                                               template_id.res_id,
                                                               ids, context)
        return True
