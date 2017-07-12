# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.osv import fields, osv
from openerp import api
import time
import datetime
from openerp.tools.translate import _

MAPPING_PRIORITIES = {'1': 'Alta', '2': 'Normale', '3': 'Bassa'}

AVAILABLE_PRIORITIES = [
    ('1', 'Alta'),
    ('2', 'Normale'),
    ('3', 'Bassa'),
]


class attivita_aggiornamenti(osv.Model):
    _name = 'attivita.aggiornamento'
    _description = 'Aggiornamenti Attivita'
    _columns = {
        'name': fields.text('Note', required=True),
        'autore_id': fields.many2one('res.users', 'Autore', required=True),
        'referente_id': fields.many2one('res.users', 'Referente'),
        'attivita_id': fields.many2one('attivita.attivita', 'Attività',
                                       required=True),
        'data_creazione': fields.date('Data Creazione', readonly=1,
                                      required=True),
        'data_lettura': fields.date('Data Lettura'),
        'state': fields.selection([('richiesto', 'Richiesto'),
                                   ('draft', 'Da Leggere'),
                                   ('letta', 'Letta'),
                                   ], 'Stato', readonly=True)
    }

    _defaults = {
        'data_creazione': lambda *a: time.strftime("%Y-%m-%d"),
        'state': 'draft',
    }

    def create(self, cr, uid, data, context=None):
        aggiornamento_id = super(attivita_aggiornamenti, self).create(cr, uid,
                                                                      data,
                                                                      context=context)
        template_model_data = self.pool.get('ir.model.data').search(cr, uid, [
            ('name', '=', 'template_email_notifica_referente_aggiornamento')])
        if len(template_model_data):
            template_id = self.pool.get('ir.model.data').browse(cr, uid,
                                                                template_model_data[
                                                                    0])
            self.pool.get('email.template').generate_email(cr, uid,
                                                           template_id.res_id,
                                                           aggiornamento_id,
                                                           context)
        return aggiornamento_id

    def segna_letto(self, cr, uid, ids, context=None):
        attivita = self.browse(cr, uid, ids[0])
        if attivita.referente_id.id == uid:
            self.write(cr, uid, ids, {'state': 'letta',
                                      'data_lettura': time.strftime(
                                          "%Y-%m-%d")})
        else:
            raise osv.except_osv(_('Attenzione!'), _(
                'Solo il referente del messaggio può marcarlo come Letto'))
        return True


class attivita_categoria(osv.Model):
    _name = 'attivita.categoria'
    _description = 'Categoria Attività'
    _columns = {
        'name': fields.char('Categoria', required=True),
        'parent_id': fields.many2one('attivita.categoria',
                                     'Categoria Superiore'),
        'descrizione': fields.text('Descrizione'),
        'attiva': fields.boolean('Attiva'),
        'tempo_standard': fields.integer(
            'Tempo Standard di Realizzazione (in gg)'),
        'singola_azione': fields.boolean(
            'Singola Azione'),
        'smistabile': fields.boolean(
            'Smistabile'),
        'automatica': fields.boolean(
            'Automatica'),
        'richiede_validazione': fields.boolean(
            'Richiede Validazione'),
    }

    _defaults = {
        'attiva': True,
    }


class attivita_attivita(osv.Model):
    _name = 'attivita.attivita'
    _description = 'Attivita'
    _date_name = "date_start"
    _inherit = ['ir.needaction_mixin']

    def _type_selection(self, cr, uid, context=None):
        return [('draft', 'Bozza'),
                ('assegnato', 'Assegnato'),
                ('lavorazione', 'Preso In Carico'),
                ('concluso', 'Concluso'),
                ('chiuso', 'Chiuso'),
                ('annullato', 'Annullato')]

    def _get_state_definition(self, cr, uid, state, context=None):
        return dict(self._type_selection(cr, uid))[state]

    def _tempo_realizzazione_calc(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for attivita in self.browse(cr, uid, ids, context=context):
            if attivita.data_conclusione and attivita.data_assegnazione:
                data_conclusione = datetime.datetime.strptime(
                    attivita.data_conclusione, '%Y-%m-%d')
                data_assegnazione = datetime.datetime.strptime(
                    attivita.data_assegnazione, '%Y-%m-%d')
                delta = data_conclusione - data_assegnazione
                res[attivita.id] = delta.days > 0 and delta.days or 0
            else:
                res[attivita.id] = 0
        return res

    def _tempo_ritardo_calc(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for attivita in self.browse(cr, uid, ids, context=context):
            if attivita.data_conclusione and attivita.data_scadenza:
                data_conclusione = datetime.datetime.strptime(
                    attivita.data_conclusione, '%Y-%m-%d')
                data_scadenza = datetime.datetime.strptime(
                    attivita.data_scadenza, '%Y-%m-%d')
                delta = data_conclusione - data_scadenza
                res[attivita.id] = delta.days > 0 and delta.days or 0
            else:
                res[attivita.id] = 0
        return res

    @api.model
    def state_groups(self, present_ids, domain, **kwargs):
        folded = {key: (key in self.FOLDED_STATES) for key, _ in self.STATES}
        return self.STATES[:], folded

    _columns = {
        'name': fields.char('Nome', required=True),
        'descrizione': fields.text("Descrizione dell'attività"),
        'ultimo_aggiornamento': fields.datetime('Data Ultimo Aggiornamento',
                                                readonly=True, required=True),
        'priorita': fields.selection(AVAILABLE_PRIORITIES, 'Priorità',
                                     select=True),
        'data_creazione': fields.date('Data Creazione', readonly=1,
                                      required=True),
        'data_assegnazione': fields.date('Data Assegnazione'),
        'data_presa_carico': fields.date('Data Presa in Carico/Rifiuto'),
        'data_scadenza': fields.date('Data Scadenza', required=True),
        'data_conclusione': fields.date('Data Conclusione'),
        'data_chiusura': fields.date('Data Chiusura'),
        'referente_id': fields.many2one('res.users', 'Referente',
                                        required=True),
        'assegnatario_id': fields.many2one('res.users', 'Assegnatario',
                                           domain="[('is_visible','=',True)]"),
        'aggiornamenti_ids': fields.one2many('attivita.aggiornamento',
                                             'attivita_id', 'Aggiornamenti'),
        'avanzamento': fields.integer('Avanzamento', group_operator="avg"),
        'motivazione_annullamento': fields.text('Motivazione Annullamento'),
        'motivazione_richiesta_integrazione': fields.text(
            'Motivazione Richiesta Integrazione'),
        'richiesta_integrazione': fields.boolean('Richiesta Integrazione'),
        'storico_ids': fields.one2many('attivita.storico', 'attivita_id',
                                       'Storico'),
        'state': fields.selection(_type_selection, 'Stato', readonly=True),
        'tempo_realizzazione': fields.function(_tempo_realizzazione_calc,
                                               type='float',
                                               string='Tempo Realizzazione',
                                               help="Calcolato dalla differenza: Data Conclusione - Data Assegnazione",
                                               store=True,
                                               group_operator="avg"),
        'tempo_ritardo': fields.function(_tempo_ritardo_calc, type='float',
                                         string='Tempo Ritardo',
                                         help="Calcolato dala differenza: Data Conclusione - Data Scadenza",
                                         store=True, group_operator="avg"),
        'categoria': fields.many2one('attivita.categoria', 'Categoria'),
        'singola_azione': fields.related('categoria',
                                     'singola_azione',
                                     type='boolean',
                                     string='Singola Azione', ),
        'smistabile': fields.related('categoria',
                                         'smistabile',
                                         type='boolean',
                                         string='Smistabile', ),
        'automatica': fields.related('categoria',
                                     'automatica',
                                     type='boolean',
                                     string='Automatica', ),
        'richiede_validazione': fields.related('categoria',
                                     'richiede_validazione',
                                     type='boolean',
                                     string='Richiede Validazione', )
    }

    _defaults = {
        'ultimo_aggiornamento': lambda *a: time.strftime("%Y-%m-%d %H:%M:%S"),
        'data_creazione': lambda *a: time.strftime("%Y-%m-%d"),
        'state': 'draft',
        'referente_id': lambda s, cr, uid, c: uid,
        'richiesta_integrazione': False,
    }

    _group_by_full = {
        'state': state_groups
    }

    STATES = [
        ('assegnato', 'Assegnato'),
        ('lavorazione', 'Preso In Carico'),
        ('concluso', 'Concluso')
    ]

    FOLDED_STATES = [
        'concluso'
    ]

    def _needaction_domain_get(self, cr, uid, context=None):
        return [('state', '=', 'assegnato'), ('assegnatario_id', '=', uid)]

    def _read_group_fill_results(self, cr, uid, domain, groupby,
                                 remaining_groupbys, aggregated_fields,
                                 count_field, read_group_result,
                                 read_group_order=None, context=None):
        if groupby == 'state':
            STATES_DICT = dict(self.STATES)
            for result in read_group_result:
                state = result['state']
                result['state'] = (state, STATES_DICT.get(state))

        return super(attivita_attivita, self)._read_group_fill_results(
            cr, uid, domain, groupby, remaining_groupbys, aggregated_fields,
            count_field, read_group_result, read_group_order, context
        )

    def write(self, cr, uid, ids, data, context=None):
        if data.has_key('state'):
            if data['state'] == 'lavorazione':
                data['assegnatario_id'] = uid
                data['data_presa_carico'] = time.strftime("%Y-%m-%d")
                data['richiesta_integrazione'] = False
                template_model_data = self.pool.get('ir.model.data').search(
                    cr, uid,
                    [('name', '=',
                      'template_email_notifica_referente_presa_carico')])
                if len(template_model_data):
                    if isinstance(ids, list):
                        ids = ids[0]
                    template_id = self.pool.get('ir.model.data').browse(
                        cr, uid, template_model_data[0])
                    self.pool.get('email.template').generate_email(
                        cr, uid, template_id.res_id, ids, context)
            elif data['state'] == 'concluso':
                data['data_conclusione'] = time.strftime("%Y-%m-%d")
                data['avanzamento'] = 100
                template_model_data = self.pool.get('ir.model.data').search(
                    cr, uid, [('name', '=',
                               'template_email_notifica_referente_chiusura')])
                if len(template_model_data):
                    if isinstance(ids, list):
                        ids = ids[0]
                    template_id = self.pool.get('ir.model.data').browse(
                        cr, uid, template_model_data[0])
                    self.pool.get('email.template').generate_email(
                        cr, uid, template_id.res_id, ids, context)
        res_id = super(attivita_attivita, self).write(cr, uid, ids, data,
                                                      context=context)
        storico_obj = self.pool.get('attivita.storico')
        user_obj = self.pool.get('res.users')
        if isinstance(ids, list):
            attivita_id = ids[0]
        else:
            attivita_id = ids
        if data.has_key('state'):
            storico_data = {
                'name': self._get_state_definition(cr, uid, data['state']),
                'attivita_id': attivita_id}
            if data['state'] == 'annullato':
                storico_data['descrizione'] = data['motivazione_annullamento']
            elif data['state'] == 'rifiutato':
                storico_data['descrizione'] = data['motivazione_rifiuto']
            elif data['state'] == 'assegnato':
                if data.has_key('richiesta_integrazione'):
                    storico_data['descrizione'] = data[
                        'motivazione_richiesta_integrazione']
                else:
                    assegnatario_name = ''
                    if data.has_key('assegnatario_id'):
                        assegnatario = user_obj.browse(cr, uid,
                                                       data['assegnatario_id'])
                        if assegnatario:
                            assegnatario_name = assegnatario.name
                    storico_data[
                        'descrizione'] = 'Assegnato a: ' + assegnatario_name
            elif data['state'] == 'lavorazione':
                storico_data[
                    'descrizione'] = 'Preso in carico da: ' + user_obj.browse(
                    cr, uid, uid).name
            elif data['state'] == 'concluso':
                storico_data[
                    'descrizione'] = 'Concluso da: ' + user_obj.browse(cr, uid,
                                                                       uid).name
            elif data['state'] == 'chiuso':
                storico_data['descrizione'] = 'Chiuso da: ' + user_obj.browse(
                    cr, uid, uid).name

            storico_obj.create(cr, uid, storico_data)
        return res_id

    def prendi_carico(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids,
                   {'assegnatario_id': uid, 'state': 'lavorazione',
                    'data_presa_carico': time.strftime("%Y-%m-%d"),
                    'richiesta_integrazione': False})
        return True

    def concludi(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'concluso',
                                  'data_conclusione': time.strftime(
                                      "%Y-%m-%d"), 'avanzamento': 100})
        if not self.browse(cr,uid,ids).richiede_validazione:
            self.valida(cr,uid,ids)
        return True

    def valida(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'chiuso',
                                  'data_chiusura': time.strftime("%Y-%m-%d")})
        return True

    def onchange_categoria(self, cr, uid, ids, categoria_id, data_assegnazione,
                           context=None):
        result = {}
        if categoria_id:
            categoria = self.pool.get('attivita.categoria').browse(cr, uid,
                                                                   categoria_id)
            if categoria.tempo_standard:
                data_partenza = data_assegnazione and datetime.datetime.strptime(
                    data_assegnazione, '%Y-%m-%d') or datetime.datetime.today()
                data_scadenza = data_partenza + datetime.timedelta(
                    days=categoria.tempo_standard)
                result = {'value': {
                    'data_scadenza': data_scadenza,
                }
                }
        return result


class attivita_storico(osv.Model):
    _name = 'attivita.storico'
    _description = 'Attivita Storico'
    _columns = {
        'name': fields.char('Evento', required=True),
        'descrizione': fields.text("Note"),
        'data_evento': fields.datetime('Data Evento', readonly=True,
                                       required=True),
        'autore': fields.many2one('res.users', 'Autore'),
        'attivita_id': fields.many2one('attivita.attivita', 'Attivita'),
    }

    _defaults = {
        'data_evento': lambda *a: time.strftime("%Y-%m-%d %H:%M:%S"),
        'autore': lambda self, cr, uid, context: uid,
    }


class res_users(osv.Model):
    _name = 'res.users'
    _inherit = ['res.users']
    _description = 'User'

    def _is_visible(self, cr, uid, ids, name, arg, context={}):
        res = {}.fromkeys(ids, '0')
        return res

    def _is_visible_search(self, cr, uid, obj, names, arg, context=None):
        return [('id', '>', 0)]

    _columns = {
        'is_visible': fields.function(_is_visible,
                                      fnct_search=_is_visible_search,
                                      type="boolean", method=True,
                                      string='Assegnatario'),

    }
