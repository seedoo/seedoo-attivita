# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
import time
from openerp.tools.translate import _


class registra_aggiornamento(osv.osv_memory):
    _name = 'attivita.registra.aggiornamento'
    _description = 'Registra Aggiornamento'

    _columns = {
        'name': fields.text('Note', required=True),
        'avanzamento_attivita': fields.boolean('Aggiorna Stato Avanzamento'),
        'avanzamento': fields.integer('Avanzamento'),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(registra_aggiornamento, self).default_get(cr, uid, fields,
                                                              context=context)
        attivita_obj = self.pool.get('attivita.attivita')
        attivita_id = context and context.get('active_id') or False
        attivita = attivita_obj.browse(cr, uid, attivita_id)
        res['avanzamento'] = attivita.avanzamento
        return res

    def registra(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        attivita_obj = self.pool.get('attivita.attivita')
        aggiornamento_obj = self.pool.get('attivita.aggiornamento')
        attivita_id = context and context.get('active_id') or False
        attivita = attivita_obj.browse(cr, uid, attivita_id)
        if attivita.assegnatario_id.id != uid:
            raise osv.except_osv(_('Attenzione!'), _(
                "Solo l'assegnatario puo' aggiornare l'attivita'!"))
        for this in self.browse(cr, uid, ids, context=context):
            aggiornamento_obj.create(cr, uid, {'name': this.name,
                                               'attivita_id': attivita_id,
                                               'referente_id': attivita.referente_id.id,
                                               'autore_id': uid})
            attivita_vals = {
                'ultimo_aggiornamento': time.strftime("%Y-%m-%d %H:%M:%S")}
            if this.avanzamento_attivita:
                attivita_vals['avanzamento'] = this.avanzamento
            attivita_obj.write(cr, uid, attivita_id, attivita_vals)
