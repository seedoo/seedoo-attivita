# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import orm
from openerp.osv import fields, osv
import logging
from openerp.osv import *
import datetime
from openerp import SUPERUSER_ID
from openerp.tools.translate import _
import time

_logger = logging.getLogger(__name__)


class attivita_categoria(osv.Model):
    _inherit = "attivita.categoria"

    _columns = {
        'protocollo': fields.boolean("Categoria di protocollo"),
        'azione': fields.many2one('ir.actions.act_window',
                                  'Azione'),
    }


class attivita_attivita(orm.Model):
    _inherit = "attivita.attivita"

    _columns = {
        'protocollo_id': fields.many2one('protocollo.protocollo', 'Protocollo',
                                         readonly=True),
        'titolario_id': fields.many2one('protocollo.classification',
                                        'Titolario', readonly=False),
        'template': fields.boolean("Template"),
        'template_instance': fields.boolean("Creato da template"),
        'protocollo': fields.related('categoria',
                                     'protocollo',
                                     type='boolean',
                                     string='Attivita di Protocollo', )
    }

    _defaults = {
        'template': False,
        'template_instance': False,
    }

    def create(self, cr, uid, data, context=None):
        if data.has_key('titolario_id') and data['titolario_id']:
            data['template'] = True
        else:
            data['template'] = False
        attivita_id = super(attivita_attivita, self).create(cr, uid, data,
                                                            context=context)
        return attivita_id

    def prendi_carico(self, cr, uid, ids, context=None):
        result = super(attivita_attivita, self).prendi_carico(cr, uid, ids, context)
        attivita = self.browse(cr, uid, ids[0])
        if attivita.categoria.azione and attivita.protocollo:
            azione = attivita.categoria.azione
            context['active_id'] = attivita.protocollo_id.id
            context['attivita_id'] = attivita.id
            return {
                'name': _("Esegui"),
                'view_mode': 'form',
                'view_id': azione.view_id.id,
                'view_type': 'form',
                'res_model': azione.res_model,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context
            }
        return result


    def synchro_protocol_action(self, context, cr, uid, module_action="", action_xml_id=""):
        # Gestione attività correlate
        attivita_ids = []
        if context.has_key('attivita_id'):
            attivita_ids = [context['attivita_id']]
        dummy, action_id = self.pool.get(
            'ir.model.data').get_object_reference(
            cr, uid, module_action, action_xml_id)
        category_ids = self.pool.get('attivita.categoria').search(cr, uid, [
            ('azione', '=', action_id)])
        attivita_ids.extend(self.search(cr, uid,
                                                [('protocollo_id', '=',
                                                  context['active_id']),
                                                 ('assegnatario_id', '=', uid),
                                                 ('categoria', 'in',
                                                  category_ids),
                                                 ('state', 'in',
                                                  ['assegnato',
                                                   'lavorazione'])]))
        for attivita_id in attivita_ids:
            self.write(cr, uid, attivita_id,
                               {'assegnatario_id': uid, 'state': 'lavorazione',
                                'data_presa_carico': time.strftime("%Y-%m-%d"),
                                'richiesta_integrazione': False})

            if self.browse(cr, uid, attivita_id).singola_azione:
                self.concludi(cr, uid, attivita_id)



class protocollo_classification(orm.Model):
    _inherit = "protocollo.classification"

    _columns = {
        'attivita_ids': fields.one2many('attivita.attivita', 'titolario_id',
                                        'Attivita', readonly=False),
    }


class protocollo_protocollo(orm.Model):
    _inherit = "protocollo.protocollo"

    _columns = {
        'attivita_ids': fields.one2many('attivita.attivita', 'protocollo_id', 'Attivita', readonly=True),
    }

    def write(self, cr, uid, ids, data, context=None):
        if isinstance(ids, (long, int)):
            ids = [ids]
        result = super(protocollo_protocollo, self).write(cr, uid, ids, data, context=context)
        for id in ids:
            prot = self.browse(cr, uid, id)
            if data.has_key('classification') and prot.state != 'draft':
                self.crea_attivita_classificazione(cr, uid, prot)
        return result

    def action_register(self, cr, uid, ids, *args):
        super(protocollo_protocollo, self).action_register(cr, uid, ids)
        # create attività
        for prot in self.browse(cr, uid, ids):
            self.crea_attivita_assegnazione(cr, uid, prot, [])
            self.crea_attivita_classificazione(cr, uid, prot)
        return True

    def crea_attivita_assegnazione(self, cr, uid, prot, old_assegnatari):
        now = datetime.datetime.now()
        attivita_obj = self.pool.get('attivita.attivita')
        categoria_obj = self.pool.get('attivita.categoria')
        category_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'seedoo_attivita', 'attivita_categoria_assegnazione')[1]

        old_assegnatari_ids = []
        for old_assegnatario in old_assegnatari:
            old_assegnatari_ids.append(old_assegnatario.id)

        # if prot.assigne_users:
        #    user_list = user_list + prot.assigne_users.ids
        assegnatari_competenza = self._get_assegnatari_competenza(cr, uid, prot)

        user_to_add = []
        for assegnatario_competenza in assegnatari_competenza:
            if assegnatario_competenza and assegnatario_competenza.user_id and not (assegnatario_competenza.id in old_assegnatari_ids):
                user_to_add.append(assegnatario_competenza.user_id.id)
        for u in list(set(user_to_add)):
            #category_ids = categoria_obj.search(cr, uid, [('name', '=', 'Assegnazione Protocollo')])
            tempo_esecuzione_attivita = 15
            category = categoria_obj.browse(cr, uid, category_id)
            tempo_esecuzione_attivita = category.tempo_standard
            data_scadenza = now + datetime.timedelta(days=tempo_esecuzione_attivita)
            user = self.pool.get('res.users').browse(cr, uid, u)
            activity_vals = {
                'name': 'Assegnazione protocollo num %s a %s ' % (prot.name, user.partner_id.name),
                'descrizione': prot.subject,
                'priorita': '3',
                'referente_id': prot.user_id.id,
                'assegnatario_id': u,
                'state': 'assegnato',
                'data_scadenza': data_scadenza,
                'data_assegnazione': now,
                'categoria': category.id,
                'protocollo_id': prot.id
            }
            # TODO we need to use the uid instead of SUPERUSER_ID
            attivita_obj.create(cr, SUPERUSER_ID, activity_vals, context=None)

        new_assegnatari_ids = []
        for assegnatario_competenza in assegnatari_competenza:
            new_assegnatari_ids.append(assegnatario_competenza.id)

        user_to_remove = []
        for old_assegnatario in old_assegnatari:
            if old_assegnatario and old_assegnatario.user_id and not (old_assegnatario.id in new_assegnatari_ids):
                user_to_remove.append(old_assegnatario.user_id.id)
        for u in list(set(user_to_remove)):
            attivita_ids = attivita_obj.search(cr, uid, [
                ('protocollo_id', '=', prot.id),
                ('assegnatario_id', '=', u),
                ('state', 'in', ['assegnato', 'lavorazione']),
                ('categoria', '=', category_id)
            ])
            if attivita_ids:
                attivita_obj.write(cr, uid, attivita_ids, {
                    'state': 'annullato',
                    'motivazione_annullamento': 'Modifica assegnazione protocollo correlato'
                })

    def crea_attivita_classificazione(self, cr, uid, prot):
        now = datetime.datetime.now()
        attivita_obj = self.pool.get('attivita.attivita')
        for attivita in prot.attivita_ids:
            if attivita.template_instance and attivita.state in ['assegnato', 'lavorazione']:
                attivita_obj.write(cr, uid, attivita.id, {
                    'state': 'annullato',
                    'motivazione_annullamento': 'Modifica classificazione protocollo correlato'
                })
        if prot.classification and len(prot.classification.attivita_ids) > 0:
            for attivita_titolario in prot.classification.attivita_ids:
                tempo_esecuzione_attivita = attivita_titolario.categoria.tempo_standard
                data_scadenza = now + datetime.timedelta(days=tempo_esecuzione_attivita)
                activity_vals = {
                    'name': 'Protocollo num %s - ' % (prot.name) + attivita_titolario.name,
                    'descrizione': attivita_titolario.descrizione,
                    'priorita': attivita_titolario.priorita,
                    'referente_id': uid,
                    'assegnatario_id': attivita_titolario.assegnatario_id.id,
                    'state': 'assegnato',
                    'data_scadenza': data_scadenza,
                    'data_assegnazione': now,
                    'categoria': attivita_titolario.categoria.id,
                    'protocollo_id': prot.id,
                    'template_instance': True,
                }
                # TODO we need to use the uid instead of SUPERUSER_ID
                attivita_obj.create(cr, SUPERUSER_ID, activity_vals, context=None)
                self.write(cr, uid, [prot.id], {'assigne_users': [(4, attivita_titolario.assegnatario_id.id)]})


    def prendi_in_carico(self, cr, uid, ids, context=None):
        attivita_obj = self.pool.get('attivita.attivita')
        result = super(protocollo_protocollo, self).prendi_in_carico(cr, uid, ids)
        dummy, category_id = self.pool.get(
            'ir.model.data').get_object_reference(
            cr, uid, 'seedoo_attivita', 'attivita_categoria_assegnazione')
        attivita_ids = attivita_obj.search(cr, uid,
                                                [('protocollo_id', '=',
                                                  ids[0]),
                                                 ('assegnatario_id', '=', uid),
                                                 ('categoria', '=',
                                                  category_id),
                                                 ('state', 'in',
                                                  ['assegnato',
                                                   'lavorazione'])])
        for attivita_id in attivita_ids:
            attivita_obj.write(cr, uid, attivita_id,
                               {'assegnatario_id': uid, 'state': 'lavorazione',
                                'data_presa_carico': time.strftime("%Y-%m-%d"),
                                'richiesta_integrazione': False})

            if attivita_obj.browse(cr, uid, attivita_id).singola_azione:
                attivita_obj.concludi(cr, uid, attivita_id)
        owner_name = self.pool.get('res.users').browse(cr,uid,uid).name
        motivazione_annullamento = 'Protocollo preso in carico da %s' %(owner_name)

        attivita_ids = attivita_obj.search(cr, SUPERUSER_ID,
                                        [('protocollo_id', '=',ids[0]),
                                         ('assegnatario_id', '!=', uid),
                                         ('categoria', '=',
                                          category_id),
                                         ('state', 'in',
                                          ['assegnato',
                                           'lavorazione'])])
        for attivita_id in attivita_ids:
            attivita_obj.write(cr, SUPERUSER_ID, attivita_id,
                               {'state': 'annullato',
                                'data_conclusione': time.strftime("%Y-%m-%d"),
                                'richiesta_integrazione': False,
                                'motivazione_annullamento': motivazione_annullamento})
        return result

    def rifiuta_presa_in_carico(self, cr, uid, ids, context=None):
        attivita_obj = self.pool.get('attivita.attivita')
        result = super(protocollo_protocollo, self).rifiuta_presa_in_carico(cr, uid, ids)
        dummy, category_id = self.pool.get(
            'ir.model.data').get_object_reference(
            cr, uid, 'seedoo_attivita', 'attivita_categoria_assegnazione')
        attivita_ids = attivita_obj.search(cr, uid,
                                                [('protocollo_id', '=',
                                                  ids[0]),
                                                 ('assegnatario_id', '=', uid),
                                                 ('categoria', '=',
                                                  category_id),
                                                 ('state', 'in',
                                                  ['assegnato',
                                                   'lavorazione'])])
        for attivita_id in attivita_ids:
            attivita_obj.write(cr, SUPERUSER_ID, attivita_id,
                               {'state': 'annullato',
                                'data_conclusione': time.strftime("%Y-%m-%d"),
                                'richiesta_integrazione': False,
                                'motivazione_annullamento': 'Rifiutata assegnazione'})
        return result