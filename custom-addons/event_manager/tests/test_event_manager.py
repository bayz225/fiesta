from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestEventManager(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organizer_user = cls.env['res.users'].create({
            'name': 'Organisateur Test',
            'login': 'organizer_test',
            'email': 'organizer@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.other_user = cls.env['res.users'].create({
            'name': 'Autre Utilisateur',
            'login': 'other_user_test',
            'email': 'other@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Responsable Test',
            'login': 'manager_user_test',
            'email': 'manager@example.com',
            'group_ids': [(6, 0, [cls.env.ref('event_manager.group_event_manager').id])],
        })
        cls.organizer = cls.organizer_user.partner_id
        cls.guest_1 = cls.env['res.partner'].create({'name': 'Invité 1'})
        cls.guest_2 = cls.env['res.partner'].create({'name': 'Invité 2'})
        cls.future_date = fields.Date.today() + timedelta(days=15)

    def _create_event(self, **kwargs):
        vals = {
            'name': 'Soirée Fiesta',
            'contact_id': self.organizer.id,
            'date': self.future_date,
            'time': 20.0,
            'location': 'Abidjan',
            'party_theme': 1,
            'max_guest': 5,
        }
        vals.update(kwargs)
        return self.env['fiesta.event'].create(vals)

    def test_event_constraints(self):
        # Date passée interdite
        with self.assertRaises(ValidationError):
            self._create_event(date=fields.Date.today() - timedelta(days=1))

        # Heure >= 24.0 interdite
        with self.assertRaises(ValidationError):
            self._create_event(time=24.0)

        # Heure 23h45 (23.75 en float_time) autorisée
        event = self._create_event(time=23.75)
        self.assertEqual(event.time, 23.75)

        # Capacité < 4 interdite
        with self.assertRaises(ValidationError):
            self._create_event(max_guest=3)

    def test_invitation_capacity_and_duplicates(self):
        from psycopg2.errors import UniqueViolation
        from odoo.tools import mute_logger

        event = self._create_event(max_guest=4)
        inv = self.env['fiesta.event.invitation'].create({
            'event_id': event.id,
            'guest_id': self.guest_1.id,
            'number_of_companions': 2,
        })
        self.assertEqual(event.total_guest, 3)
        self.assertEqual(event.available_places_int, 1)

        # Doublon interdit (Isolé dans un savepoint !)
        with mute_logger('odoo.sql_db'), self.env.cr.savepoint(), self.assertRaises(UniqueViolation):
            self.env['fiesta.event.invitation'].create({
                'event_id': event.id,
                'guest_id': self.guest_1.id,
            })
            self.env.flush_all() # Force l'envoi de l'ordre INSERT à PostgreSQL

        # Dépassement de capacité interdit
        with self.assertRaises(ValidationError):
            inv.write({'number_of_companions': 4})

    def test_confirmation_deadline_blocks_all(self):
        # Créer un événement loin puis l'invité avant de rapprocher la date limite
        event = self._create_event(date=fields.Date.today() + timedelta(days=10))
        inv = self.env['fiesta.event.invitation'].create({
            'event_id': event.id,
            'guest_id': self.guest_1.id,
        })

        # Rapprocher la date de l'événement dans la fenêtre de 5 jours
        event.write({'date': fields.Date.today() + timedelta(days=2)})

        # Forcer le recalcul du champ compute
        inv.invalidate_recordset(['is_expired_confirmation'])

        self.assertTrue(inv.is_expired_confirmation)

        # La modification des informations est bloquée
        with self.assertRaises(ValidationError):
            inv.write({'number_of_companions': 1})

        # L'ajout d'un nouvel invité est également bloqué
        with self.assertRaises(ValidationError):
            self.env['fiesta.event.invitation'].create({
                'event_id': event.id,
                'guest_id': self.guest_2.id,
            })

    def test_arrival_time_buffer(self):
        event = self._create_event(time=18.0)
        with self.assertRaises(ValidationError):
            self.env['fiesta.event.invitation'].create({
                'event_id': event.id,
                'guest_id': self.guest_1.id,
                'arrival_time': 21.0,
            })

        inv = self.env['fiesta.event.invitation'].create({
            'event_id': event.id,
            'guest_id': self.guest_1.id,
            'arrival_time': 19.5,
        })
        self.assertEqual(inv.arrival_time, 19.5)

    def test_event_record_rules(self):
        event = self._create_event()

        # Un tiers non invité ne peut ni lire, ni modifier, ni supprimer l'événement
        self.env.invalidate_all()
        event_as_other = event.with_user(self.other_user)
        with self.assertRaises(AccessError):
            _ = event_as_other.name
        with self.assertRaises(AccessError):
            event_as_other.write({'name': 'Modifié'})
        with self.assertRaises(AccessError):
            event_as_other.unlink()

        # Un utilisateur interne ne peut pas créer un événement pour quelqu'un d'autre
        with self.assertRaises(AccessError):
            self.env['fiesta.event'].with_user(self.other_user).create({
                'name': 'Événement pour autrui',
                'contact_id': self.organizer.id,
                'date': self.future_date,
                'time': 20.0,
                'location': 'Abidjan',
                'max_guest': 5,
            })

        # Un utilisateur interne peut créer un événement pour lui-même
        own_event = self.env['fiesta.event'].with_user(self.other_user).create({
            'name': 'Mon événement',
            'contact_id': self.other_user.partner_id.id,
            'date': self.future_date,
            'time': 20.0,
            'location': 'Abidjan',
            'max_guest': 5,
        })
        self.assertEqual(own_event.name, 'Mon événement')
        own_event.unlink()

        # Tant que l'événement est en brouillon, un invité ne peut pas encore le lire
        self.env['fiesta.event.invitation'].create({
            'event_id': event.id,
            'guest_id': self.other_user.partner_id.id,
        })
        with self.assertRaises(AccessError):
            _ = event_as_other.name

        # Une fois l'événement confirmé, l'invité peut le lire mais pas le modifier ni le supprimer
        event.with_user(self.organizer_user).action_confirm()
        self.assertEqual(event_as_other.name, 'Soirée Fiesta')
        with self.assertRaises(AccessError):
            event_as_other.write({'name': 'Modifié'})
        with self.assertRaises(AccessError):
            event_as_other.unlink()

        # Un Responsable Événements peut créer pour autrui et modifier tout événement
        mgr_event = self.env['fiesta.event'].with_user(self.manager_user).create({
            'name': 'Créé par Manager',
            'contact_id': self.organizer.id,
            'date': self.future_date,
            'time': 20.0,
            'location': 'Abidjan',
            'max_guest': 5,
        })
        mgr_event.unlink()
        event_as_manager = event.with_user(self.manager_user)
        event_as_manager.write({'name': 'Modifié par Responsable'})
        self.assertEqual(event.name, 'Modifié par Responsable')

        # L'organisateur peut lire, modifier et supprimer
        event_as_org = event.with_user(self.organizer_user)
        self.assertEqual(event_as_org.name, 'Modifié par Responsable')
        event_as_org.write({'name': 'Soirée Mise à Jour'})
        self.assertEqual(event.name, 'Soirée Mise à Jour')
        event_as_org.unlink()

    def test_invitation_record_rules_and_state_workflow(self):
        event = self._create_event()
        self.assertEqual(event.state, 'draft')

        event.with_user(self.organizer_user).action_confirm()
        self.assertEqual(event.state, 'confirmed')

        inv = self.env['fiesta.event.invitation'].with_user(self.organizer_user).create({
            'event_id': event.id,
            'guest_id': self.other_user.partner_id.id,
        })
        inv_guest1 = self.env['fiesta.event.invitation'].with_user(self.organizer_user).create({
            'event_id': event.id,
            'guest_id': self.guest_1.id,
        })

        # Un tiers (ni organisateur ni invité) ne peut pas lire/modifier/supprimer l'invitation
        third_user = self.env['res.users'].create({
            'name': 'Tiers Test',
            'login': 'third_user_test',
            'email': 'third@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.env.invalidate_all()
        with self.assertRaises(AccessError):
            _ = inv.with_user(third_user).number_of_companions
        with self.assertRaises(AccessError):
            inv.with_user(third_user).write({'number_of_companions': 1})
        with self.assertRaises(AccessError):
            inv.with_user(third_user).unlink()

        # L'invité peut consulter la liste des invités mais pas modifier/supprimer celle d'un autre
        self.assertEqual(inv_guest1.with_user(self.other_user).guest_id, self.guest_1)
        with self.assertRaises(AccessError):
            inv_guest1.with_user(self.other_user).write({'number_of_companions': 1})
        with self.assertRaises(AccessError):
            inv.with_user(self.other_user).unlink()

        # L'invité peut modifier sa propre invitation
        inv.with_user(self.other_user).write({'number_of_companions': 1})
        self.assertEqual(inv.number_of_companions, 1)

        # L'organisateur peut supprimer une invitation
        inv_guest1.with_user(self.organizer_user).unlink()

        # Annulation bloque de nouvelles invitations
        event.with_user(self.organizer_user).action_cancel()
        self.assertEqual(event.state, 'cancelled')
        with self.assertRaises(ValidationError):
            self.env['fiesta.event.invitation'].create({
                'event_id': event.id,
                'guest_id': self.guest_1.id,
            })

        event.with_user(self.organizer_user).action_reset_draft()
        self.assertEqual(event.state, 'draft')

    def test_dashboard_empty_and_partner_event_list(self):
        # Aucun événement existant : pas de ZeroDivisionError
        self.env['fiesta.event'].search([]).unlink()
        data = self.env['fiesta.event.dashboard'].get_tiles_data()
        self.assertEqual(data['count_all_events'], 0)
        self.assertEqual(data['percentage_of_created_events_last_7_days'], 0.0)
        self.assertEqual(data['percentage_of_events_fully_booked'], 0.0)

        # event_list inclut les événements organisés ET les invitations reçues
        event_org = self._create_event()
        self.assertIn(event_org, self.organizer.event_list)
        self.env['fiesta.event.invitation'].create({
            'event_id': event_org.id,
            'guest_id': self.guest_1.id,
        })
        self.assertIn(event_org, self.guest_1.event_list)

    def test_wizards(self):
        event = self._create_event(time=19.0, max_guest=4)
        event.with_user(self.organizer_user).action_confirm()

        # Wizard ajout de contacts
        contact_wiz = self.env['add.contact.to.event.wizard'].create({
            'event_id': event.id,
            'line_ids': [(0, 0, {'guest_id': self.guest_1.id})],
        })
        contact_wiz.action_add_contacts()
        self.assertEqual(event.total_guest, 1)

        # Wizard info invité : 1 invité + 3 accompagnants = 4 -> échoue car il reste 3 places
        guest_wiz = self.env['add.guest.info.to.event.wizard'].create({
            'event_id': event.id,
            'guest_id': self.guest_2.id,
            'arrival_time': 19.5,
            'number_of_companions': 3,
        })
        with self.assertRaises(ValidationError):
            guest_wiz.action_add_guest_info()

        # Wizard info invité : 1 invité + 1 accompagnant = 2 -> autorisé
        guest_wiz_ok = self.env['add.guest.info.to.event.wizard'].create({
            'event_id': event.id,
            'guest_id': self.guest_2.id,
            'arrival_time': 19.5,
            'number_of_companions': 1,
        })
        guest_wiz_ok.action_add_guest_info()
        self.assertEqual(event.total_guest, 3)

    def test_dashboard_tiles_data(self):
        from dateutil.relativedelta import relativedelta

        self.env['fiesta.event'].search([]).unlink()
        self.env.cr.flush() # Force PostgreSQL à vider les données avant de continuer le test
        today = fields.Date.context_today(self.env.user)
        last_day_current_month = today.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
        next_month_date = last_day_current_month + timedelta(days=5)

        ev_active = self._create_event(name='Actif ce mois', date=last_day_current_month)
        ev_cancelled = self._create_event(name='Annulé ce mois', date=today)
        ev_cancelled.with_user(self.manager_user).action_cancel()
        self._create_event(name='Mois prochain', date=next_month_date)

        data = self.env['fiesta.event.dashboard'].with_context(lang='fr_FR').get_tiles_data()
        self.assertEqual(data['count_upcoming_events'], 1)
        self.assertEqual(data['count_events_of_this_month'], 1)
        self.assertEqual(data['percentage_of_events_this_month'], 100.0)
        self.assertEqual(len(data['chart_values']), 6)
        self.assertTrue(ev_active.exists())
