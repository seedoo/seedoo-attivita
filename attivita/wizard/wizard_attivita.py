# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
import time
from openerp.tools.translate import _


class wizard_attivita(osv.osv_memory):
    _name = 'attivita.wizard.attivita'
    _description = 'Wizard Attivita'

    _columns = {
        'name': fields.text('Note', required=True),
        'case': fields.selection([('rifiuto', 'Rifiuto'),
                                  ('annulla', 'Annullamento'),
                                  ('integrazione', 'Integrazione')], 'Caso',
                                 readonly=True)
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(wizard_attivita, self).default_get(cr, uid, fields,
                                                       context=context)
        if 'case' in context.keys():
            res['case'] = context['case']
        return res

    def rifiuta(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        attivita_obj = self.pool.get('attivita.attivita')
        attivita_id = context and context.get('active_id') or False
        for this in self.browse(cr, uid, ids, context=context):
            attivita_obj.write(cr, uid, attivita_id, {'state': 'rifiutato',
                                                      'motivazione_rifiuto': this.name})
            template_model_data = self.pool.get('ir.model.data'). \
                search(cr, uid, [('name', '=',
                                  'template_email_notifica_referente_rifiuto')])
            if len(template_model_data):
                template_id = self.pool.get('ir.model.data').browse(cr,
                                                                    uid,
                                                                    template_model_data[
                                                                        0])
                self.pool.get('email.template').generate_email(cr, uid,
                                                               template_id.res_id,
                                                               attivita_id,
                                                               context)

    def integrazione(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        attivita_obj = self.pool.get('attivita.attivita')
        attivita_id = context and context.get('active_id') or False
        for this in self.browse(cr, uid, ids, context=context):
            attivita_obj.write(cr, uid, attivita_id, {'state': 'lavorazione',
                                                      'motivazione_richiesta_integrazione': this.name,
                                                      'richiesta_integrazione': True})

    def annulla(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        attivita_obj = self.pool.get('attivita.attivita')
        attivita_id = context and context.get('active_id') or False
        for this in self.browse(cr, uid, ids, context=context):
            attivita_obj.write(cr, uid, attivita_id, {'state': 'annullato',
                                                      'motivazione_annullamento': this.name})
            template_model_data = self.pool.get('ir.model.data'). \
                search(cr, uid, [('name', '=',
                                  'template_email_notifica_assegnatario_annullamento')])
            if len(template_model_data):
                template_id = self.pool.get('ir.model.data'). \
                    browse(cr, uid, template_model_data[0])
                self.pool.get('email.template').generate_email(cr, uid,
                                                               template_id.res_id,
                                                               attivita_id,
                                                               context)
