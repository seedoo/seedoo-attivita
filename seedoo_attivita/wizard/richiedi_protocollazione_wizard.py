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


class document_request_sender_receiver_wizard(osv.TransientModel):
    _name = 'document.request.sender_receiver.wizard'

    _columns = {
        # TODO: inserire anche AOO in type?
        'wizard_id': fields.many2one('gedoc.document.richiesta.wizard',
                                     'Crea Protocollo'),
        'type': fields.selection(
            [
                ('individual', 'Persona Fisica'),
                ('legal', 'Azienda privata'),
                ('government', 'Amministrazione pubblica')
            ], 'Tipologia', size=32, required=True),

        'ident_code': fields.char(
            'Codice Identificativo Area',
            size=256,
            required=False),

        'ammi_code': fields.char(
            'Codice Amministrazione',
            size=256,
            required=False),

        'save_partner': fields.boolean(
            'Salva',
            help='Se spuntato salva i dati in anagrafica.'),
        'partner_id': fields.many2one('res.partner', 'Anagrafica',
                                      domain="[('legal_type', '=', type)]"),
        'name': fields.char('Nome Cognome/Ragione Sociale',
                            size=512,
                            required=True),
        'street': fields.char('Via/Piazza num civico', size=128),
        'zip': fields.char('Cap', change_default=True, size=24),
        'city': fields.char('Citta\'', size=128),
        'country_id': fields.many2one('res.country', 'Paese'),
        'email': fields.char('Email', size=240),
        'pec_mail': fields.char('PEC', size=240),
        'phone': fields.char('Telefono', size=64),
        'fax': fields.char('Fax', size=64),
        'mobile': fields.char('Cellulare', size=64),
        'notes': fields.text('Note'),
        'send_type': fields.many2one(
            'protocollo.typology', 'Canale di Spedizione'),
        'send_date': fields.date('Data Spedizione'),
        'protocol_state': fields.related('protocollo_id',
                                         'state',
                                         type='char',
                                         string='State',
                                         readonly=True),
    }

    _defaults = {
        'type': 'individual',
    }

    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        values = {}
        if partner_id:
            partner = self.pool.get('res.partner'). \
                browse(cr, uid, partner_id, context=context)
            values = {
                # 'type': partner.is_company and 'individual' or 'legal',
                'type': partner.legal_type,
                'ident_code': partner.ident_code,
                'ammi_code': partner.ammi_code,
                'name': partner.name,
                'street': partner.street,
                'city': partner.city,
                'country_id': (
                    partner.country_id and
                    partner.country_id.id or False),
                'email': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'pec_mail': partner.pec_mail,
                'fax': partner.fax,
                'zip': partner.zip,
                'save_partner': False,
            }
        return {'value': values}

    class wizard(osv.TransientModel):
        """
            Wizard per la richiesta di protocollo
        """
        _name = 'gedoc.document.richiesta.wizard'
        _description = 'Richiedi Protocollo Wizard'

        STATE_SELECTION = [
            ('draft', 'Compilazione'),
            ('protocol', 'Da protocollare'),
        ]

        _columns = {
            'typology': fields.many2one('protocollo.typology', 'Mezzo di Trasmissione', required=True,
                                        help="Tipologia invio/ricevimento: Raccomandata, Fax, PEC, etc. si possono inserire nuove tipologie dal menu Tipologie."),
            'user_id': fields.many2one('res.users', 'Protocollatore', required=True),
            'sender_receivers': fields.one2many(
                'document.request.sender_receiver.wizard',
                'wizard_id',
                'Destinatari',
                required=True),

            'note_protocollazione': fields.text('Note Protocollazione', required=True),
            'receiving_date': fields.datetime('Data Ricezione', required=True),
            'state': fields.selection(STATE_SELECTION, 'Stato', readonly=True, help="Lo stato del documento.",
                                      select=True)
        }

        def action_request(self, cr, uid, ids, context=None):
            wizard = self.browse(cr, uid, ids[0], context=context)
            sender_receiver_obj = self.pool.get('protocollo.sender_receiver')
            ir_attachment_obj = self.pool.get('ir.attachment')
            protocollo_typology_obj = self.pool.get('protocollo.typology')

            # creo i sender_receivers
            sender_receiver = []
            for send_rec in wizard.sender_receivers:
                srvals = {
                    'type': send_rec.type,
                    'partner_id': send_rec.partner_id and
                                  send_rec.partner_id.id or False,
                    'name': send_rec.name,
                    'street': send_rec.street,
                    'zip': send_rec.zip,
                    'city': send_rec.city,
                    'country_id': send_rec.country_id and
                                  send_rec.country_id.id or False,
                    'email': send_rec.email,
                    'pec_mail': send_rec.pec_mail,
                    'phone': send_rec.phone,
                    'fax': send_rec.fax,
                    'mobile': send_rec.mobile,
                }
                sender_receiver.append(sender_receiver_obj.create(cr, uid, srvals))
            if 'active_id' in context.keys():
                gedoc_obj = self.pool.get('gedoc.document')
                gedoc = gedoc_obj.browse(cr, uid, context['active_id'])
                
        # crea l'istanza protocollo
            protocollo_vals = {
                'subject': gedoc.subject,
                'receiving_date': wizard.receiving_date,
                'user_id': wizard.user_id.id,
                'notes': wizard.note_protocollazione,
                'sender_receivers': [(6, 0, sender_receiver)],
                'typology': wizard.typology.id,
                'type': 'out',
                'doc_id': gedoc.main_doc_id.id,
                'datas_fname': gedoc.main_doc_id.name,
                'mimetype': gedoc.main_doc_id.file_type,
                'datas': gedoc.main_doc_id.datas,
                'protocol_request': True
            }
            prot_id = self.pool.get("protocollo.protocollo").create(cr, SUPERUSER_ID, protocollo_vals, context=None)

        # crea attività
            prot = self.pool.get('protocollo.protocollo').browse(cr, uid, prot_id)
            user_value = self.pool.get('res.users').browse(cr, uid, uid)
            now = datetime.datetime.now()
            categoria_obj = self.pool.get('attivita.categoria')
            category_ids = categoria_obj.search(cr, uid, [('name', '=', 'Richiesta Protocollazione Documento')])
            if len(category_ids) == 1:
                category = categoria_obj.browse(cr, uid, category_ids[0])
                tempo_esecuzione_attivita = category.tempo_standard
            data_scadenza = now + datetime.timedelta(days=tempo_esecuzione_attivita)
            assegnatario_id = wizard.user_id.id

        # cambia lo stato del documento
            if 'active_id' in context.keys():
                gedoc_obj = self.pool.get('gedoc.document')
                gedoc_obj.write(cr, SUPERUSER_ID, [context['active_id']], {'user_comp_ids': [(4,assegnatario_id)], 'state': 'protocol'})
            
                gedoc = gedoc_obj.browse(cr, uid, context['active_id'])
                activity_vals = {
                    'name': "Richiesta protocollazione documento %s da %s " % (gedoc.name, user_value.login),
                    'descrizione': gedoc.subject,
                    'priorita': '3',
                    'referente_id': wizard.user_id.id,
                    'assegnatario_id': assegnatario_id,
                    'state': 'assegnato',
                    'data_scadenza': data_scadenza,
                    'data_assegnazione': now,
                    'data_presa_carico': now,
                    'categoria': category.id,
                    'protocollo_id': prot.id
                }
                gedoc_obj.pool.get("attivita.attivita").create(cr, SUPERUSER_ID, activity_vals, context=None)

            return {'type': 'ir.actions.act_window_close'}
