# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import osv


class protocollo_assegna_wizard(osv.TransientModel):
    _inherit = 'protocollo.assegna.wizard'

    def action_save(self, cr, uid, ids, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        protocollo = protocollo_obj.browse(cr, uid, context['active_id'])
        old_assegnatari = protocollo_obj._get_assegnatari_competenza(cr, uid, protocollo)

        result = super(protocollo_assegna_wizard, self).action_save(cr, uid, ids, context)

        protocollo = protocollo_obj.browse(cr, uid, context['active_id'])
        protocollo_obj.crea_attivita_assegnazione(cr, uid, protocollo, old_assegnatari)

        return result