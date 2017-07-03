# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm
from openerp.osv import fields, osv
import logging
from openerp.osv import *
import datetime
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _

from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class gedoc_document(osv.Model):
    _inherit = 'gedoc.document'

    STATE_SELECTION = [
        ('draft', 'Compilazione'),
        ('protocol', 'Da protocollare'),
    ]
    _columns = {
        'state': fields.selection(STATE_SELECTION, 'Stato', readonly=True,
                                  help="Lo stato del documento.", select=True)
    }

    _defaults = {
        'state': 'draft',
    }

    def _get_user_name(self, cr, uid, *args):
        user_obj = self.pool.get('res.users')
        user_value = user_obj.browse(cr, uid, uid)
        return user_value.login or False

    def generate_msg(self, cr, uid, ids, context=None):
        raise osv.except_osv(_("Warning!"), _("Inserire un allegato !!."))

    def richiedi_protocollazione(self, cr, uid, ids, context=None):
        for gedoc in self.browse(cr, uid, ids[0], context):
            # crea l'istanza protocollo
            protocollo_vals = {
                'subject': gedoc.note_protocollazione,
                'sender_receivers': [(6, 0, gedoc.sender_receiver_ids.ids)],
                'typology': gedoc.typology.id,
                'type': 'out',
                'doc_id': gedoc.main_doc_id.id,
                'datas_fname': gedoc.main_doc_id.name,
                'mimetype': gedoc.main_doc_id.file_type,
                'datas': gedoc.main_doc_id.datas
            }
            prot_id = self.pool.get("protocollo.protocollo").create(cr, uid,
                                                                    protocollo_vals,
                                                                    context=None)

            # crea attività
            prot = self.pool.get('protocollo.protocollo').browse(cr, uid,
                                                                 prot_id)
            user_value = self.pool.get('res.users').browse(cr, uid, uid)
            now = datetime.datetime.now()
            categoria_obj = self.pool.get('attivita.categoria')
            category_ids = categoria_obj.search(cr, uid, [
                ('name', '=', 'Richiesta Protocollazione Documento')])
            if len(category_ids) == 1:
                category = categoria_obj.browse(cr, uid, category_ids[0])
                tempo_esecuzione_attivita = category.tempo_standard
            data_scadenza = now + datetime.timedelta(
                days=tempo_esecuzione_attivita)

            users_manager = self.pool.get('res.users').get_users_from_group(cr,
                                                                            uid,
                                                                            'Manager protocollo')
            list_ids = list(users_manager.ids)
            list_ids.remove(SUPERUSER_ID)
            assegnatario_id = list_ids[0]

            activity_vals = {
                'name': "Richiesta protocollazione protocollo num %s da %s " % (
                    prot.name, user_value.login),
                'descrizione': gedoc.subject,
                'priorita': '3',
                'referente_id': prot.user_id.id,
                'assegnatario_id': assegnatario_id,
                'state': 'assegnato',
                'data_scadenza': data_scadenza,
                'data_assegnazione': now,
                'data_presa_carico': now,
                'categoria': category.id,
                'protocollo_id': prot.id
            }
            self.pool.get("attivita.attivita").create(cr, uid, activity_vals,
                                                      context=None)
            self.write(cr, uid, [gedoc.id], {'state': 'protocol'})
        return True


class sender_receiver(osv.Model):
    _inherit = 'protocollo.sender_receiver'
