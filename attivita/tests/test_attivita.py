# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from openerp.tests.common import TransactionCase
import logging
import datetime

from openerp import SUPERUSER_ID


class TestAttivita(TransactionCase):

    def setUp(self):
        super(TestAttivita, self).setUp()
        self.attivita_model = self.registry('attivita.attivita')
        self.attivita_storico_model = self.registry('attivita.storico')
        self.res_groups_model = self.registry('res.groups')
        self.res_users_model = self.registry('res.users')
        self.res_dep_model = self.registry('hr.department')
        self.res_emp_model = self.registry('hr.employee')
        self.ir_module_model = self.registry('ir.module.module')
        self.monitor_group_name = 'Monitoraggio Attivita'
        self.ref_group_name = 'Referente Attivita'
        self.assignee_group_name = u'Assegnatario Attività'

        self._logger = logging.getLogger(__name__)

    def _get_visibility_users(self, cr, uid, vis_type, context=None):
        return dict(self._visibility_selection())[vis_type]

    def _visibility_selection(self):
        return [('totale', 4),
                ('gerarchico', 6),
                ('orizzontale', 6)]

    def _get_state_definition(self, cr, uid, state, context=None):
        return dict(self._type_selection(cr, uid))[state]

    def _type_selection(self, cr, uid, context=None):
        return [('draft', 'Bozza'),
                ('assegnato', 'Assegnato'),
                ('lavorazione', 'Preso In Carico'),
                ('concluso', 'Concluso'),
                ('chiuso', 'Chiuso'),
                ('annullato', 'Annullato'),
                ('rifiutato', 'Rifiutato')]

    def test_name_search(self):
        self.assertEqual(5, 5,
                         "name_search 'ilike Tax' should have returned Tax Received account only")

    def test_user_monitor_activity(self):
        cr, uid = self.cr, self.uid
        activity_monitor_group_id = self.res_groups_model.search(cr, uid, [
            ('name', '=', self.monitor_group_name)])

        self._logger.info(
            "activity_monitor_group_id %s" % activity_monitor_group_id)

        data = {

            'name': 'TestMonitor',
            'login': 'testMonitor',
            'alias_name': 'testMonitor',
            'email': 'test.monitor@test.srd',
            'groups_id': [(6, 0, activity_monitor_group_id)]
        }

        user_id = self.res_users_model.create(cr, uid, data)

        activity_ids = self.attivita_model.search(cr, SUPERUSER_ID, [])

        user_activity_ids = self.attivita_model.search(cr, user_id, [])

        self.assertEqual(len(activity_ids), len(user_activity_ids),
                         "activiy list should be equal")

    def test_user_assignee_activity(self):
        cr, uid = self.cr, self.uid
        activity_assignee_group_id = self.res_groups_model.search(cr, uid, [
            ('name', '=', self.assignee_group_name)])

        self._logger.info(
            "activity_assignee_group_id %s" % activity_assignee_group_id)

        data = {

            'name': 'TestAssignee',
            'login': 'testAssignee',
            'alias_name': 'testAssignee',
            'email': 'test.assignee@test.srd',
            'groups_id': [(6, 0, activity_assignee_group_id)]
        }

        user_id = self.res_users_model.create(cr, uid, data)
        now = datetime.datetime.now()
        data_scadenza = now + datetime.timedelta(days=15)

        for i in [1, 2]:
            activity_vals = {
                'name': 'Test assegnee %s' % i,
                'descrizione': 'Test assegnee %s' % i,
                'priorita': '3',
                'referente_id': SUPERUSER_ID,
                'assegnatario_id': user_id,
                'state': 'assegnato',
                'data_scadenza': data_scadenza,
                'data_assegnazione': now,
                'data_presa_carico': now
            }

            self.attivita_model.create(cr, uid, activity_vals)

        activity_ids = self.attivita_model.search(cr, SUPERUSER_ID, [
            ('assegnatario_id', '=', user_id)])

        user_activity_ids = self.attivita_model.search(cr, user_id, [])

        self.assertEqual(len(activity_ids), len(user_activity_ids),
                         "activiy list should be equal")

    def test_user_ref_activity(self):
        cr, uid = self.cr, self.uid
        activity_ref_group_id = self.res_groups_model.search(cr, uid, [
            ('name', '=', self.ref_group_name)])

        self._logger.info("activity_ref_group_id %s" % activity_ref_group_id)

        data = {

            'name': 'TestRef',
            'login': 'testRef',
            'alias_name': 'testRef',
            'email': 'test.ref@test.srd',
            'groups_id': [(6, 0, activity_ref_group_id)]
        }

        user_id = self.res_users_model.create(cr, uid, data)
        now = datetime.datetime.now()
        data_scadenza = now + datetime.timedelta(days=15)

        for i in [1, 2]:
            activity_vals = {
                'name': 'Test assegnee %s' % i,
                'descrizione': 'Test assegnee %s' % i,
                'priorita': '3',
                'referente_id': user_id,
                'assegnatario_id': SUPERUSER_ID,
                'state': 'assegnato',
                'data_scadenza': data_scadenza,
                'data_assegnazione': now,
                'data_presa_carico': now
            }

            self.attivita_model.create(cr, uid, activity_vals)

        activity_ids = self.attivita_model.search(cr, SUPERUSER_ID, [
            ('referente_id', '=', user_id)])

        user_activity_ids = self.attivita_model.search(cr, user_id, [])

        self.assertEqual(len(activity_ids), len(user_activity_ids),
                         "activiy list should be equal")

    def test_activiy_history(self):
        cr, uid = self.cr, self.uid
        now = datetime.datetime.now()
        data_scadenza = now + datetime.timedelta(days=15)

        activity_vals = {
            'name': 'Test assegnee',
            'descrizione': 'Test assegnee',
            'priorita': '3',
            'referente_id': SUPERUSER_ID,
            'assegnatario_id': SUPERUSER_ID,
            'state': 'draft',
            'data_scadenza': data_scadenza,
            'data_assegnazione': now,
            'data_presa_carico': now
        }

        attivita_id = self.attivita_model.create(cr, uid, activity_vals)

        for s in ['assegnato', 'lavorazione', 'concluso', 'chiuso',
                  'annullato']:
            activity_vals = {
                'state': s,
            }

            if s == 'annullato':
                activity_vals[
                    'motivazione_annullamento'] = 'test motivazione_annullamento'

            self.attivita_model.write(cr, uid, attivita_id, activity_vals)

            ids = self.attivita_storico_model.search(cr, uid, [
                ('attivita_id', '=', attivita_id),
                ('name', '=ilike', self._get_state_definition(cr, uid, s))])
            self.assertTrue(bool(ids))

        attivita_rifiouto_module_installed = self.ir_module_model.search(
            cr, uid,
            [('name', '=', 'attivita_rifiuto'), ('state', '=', 'installed')])
        
        if attivita_rifiouto_module_installed:
            activity_vals = {
                'state': 'rifiutato',
                'motivazione_rifiuto': 'test motivazione_rifiuto'
            }
            self.attivita_model.write(cr, uid, attivita_id, activity_vals)

            ids = self.attivita_storico_model.search(cr, uid, [
                ('attivita_id', '=', attivita_id),
                ('name', '=ilike', self._get_state_definition(cr, uid, s))])
            self.assertTrue(bool(ids))

    def test_activiy_visibility_search(self):
        cr, uid = self.cr, self.uid

        existing_usr_on_system_ids = self.res_users_model.search(cr, uid, [])

        existing_usr_on_system_num = len(existing_usr_on_system_ids)

        # Departments
        vals = {
            'name': 'Direzione',
            'company_id': 1,
            'assignable': True,
            'desc': 'Direzione'
        }

        direzione_id = self.res_dep_model.create(cr, uid, vals)

        vals = {
            'name': 'Amministrazione',
            'company_id': 1,
            'assignable': True,
            'parent_id': direzione_id,
            'desc': 'Amministrazione'
        }

        amministrazione_id = self.res_dep_model.create(cr, uid, vals)

        vals = {
            'name': 'Contabilita',
            'company_id': 1,
            'assignable': True,
            'parent_id': amministrazione_id,
            'desc': 'Contabilita'
        }

        contabilita_id = self.res_dep_model.create(cr, uid, vals)

        # USERS AND EMPS
        self._create_emp(cr, uid, direzione_id, 'Direzione')
        admin1_id = self._create_emp(cr, uid, amministrazione_id,
                                     'Amministrazione1')
        self._create_emp(cr, uid, amministrazione_id, 'Amministrazione2')
        self._create_emp(cr, uid, contabilita_id, 'Contabilita')

        for i in ['totale', 'gerarchico', 'orizzontale']:
            ids = self.res_users_model.search(cr, admin1_id,
                                              [('is_visible', '=', True)])
            n = self._get_visibility_users(cr, uid, i)
            if i == 'totale':
                n = n + existing_usr_on_system_num

            self.assertEquals(len(ids), n,
                              "User with visiility type configuration [%s] must see %s users" % (
                                  i, n))

    def _create_emp(self, cr, uid, department_id, name):

        data = {

            'name': name,
            'login': name,
            'alias_name': name,
            'email': '%s@test.srd' % name,
        }

        user_id = self.res_users_model.create(cr, uid, data)

        emp_vals = {
            'message_follower_ids': False,
            'address_id': 1,
            'coach_id': False,
            'marital': False,
            'identification_id': False,
            'bank_account_id': False,
            'user_id': user_id,
            'job_id': False,
            'work_phone': False,
            'country_id': False,
            'company_id': 1,
            'category_ids': [[6, False, []]],
            'parent_id': False,
            'department_id': department_id,
            'otherid': False,
            'mobile_phone': False,
            'birthday': False,
            'active': True,
            'work_email': 'work.mail@test.srd',
            'work_location': False,
            'image_medium': False,
            'name': 'TestAssegneeDep',
            'gender': False,
            'notes': False,
            'address_home_id': False,
            'message_ids': False,
            'passport_id': False
        }

        self.res_emp_model.create(cr, uid, emp_vals)

        return user_id

    def tearDown(self):
        pass
