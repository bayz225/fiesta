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
        event = self._create_event(max_guest=4)
        inv = self.env['fiesta.event.invitation'].create({
            'event_id': event.id,
            'guest_id': self.guest_1.id,
            'number_of_companions': 2,
        })
        self.assertEqual(event.total_guest, 3)
        self.assertEqual(event.available_places_int, 1)

        # Doublon interdit
        with self.assertRaises(ValidationError):
            self.env['fiesta.event.invitation'].create({
                'event_id': event.id,
                'guest_id': self.guest_1.id,
            })

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

        # Un autre utilisateur interne peut lire mais pas modifier ni supprimer
        event_as_other = event.with_user(self.other_user)
        self.assertEqual(event_as_other.name, 'Soirée Fiesta')
        with self.assertRaises(AccessError):
            event_as_other.write({'name': 'Modifié'})
        with self.assertRaises(AccessError):
            event_as_other.unlink()

        # L'organisateur peut modifier et supprimer
        event_as_org = event.with_user(self.organizer_user)
        event_as_org.write({'name': 'Soirée Mise à Jour'})
        self.assertEqual(event.name, 'Soirée Mise à Jour')
        event_as_org.unlink()

    def test_tiles_data_empty_and_event_list(self):
        # Aucun événement existant : pas de ZeroDivisionError
        self.env['fiesta.event'].search([]).unlink()
        data = self.env['res.partner'].get_tiles_data()
        self.assertEqual(data['all_events_count'], 0)
        self.assertEqual(data['all_events_last_week_percentage'], 0.0)
        self.assertEqual(data['all_events_fully_percentage'], 0.0)

        # event_list inclut les événements organisés ET les invitations
        event_org = self._create_event()
        self.assertIn(event_org, self.organizer.event_list)

    def test_wizards(self):
        # Wizard création d'événement
        add_wiz = self.env['add.event.wizard'].with_context(
            active_model='res.partner',
            active_id=self.organizer.id,
        ).create({
            'name': 'Événement Wizard',
            'date': self.future_date,
            'time': 19.0,
            'location': 'Plateau',
            'party_theme': 2,
            'max_guest': 4,
        })
        add_wiz.action_add_event()
        event = self.env['fiesta.event'].search([('name', '=', 'Événement Wizard')], limit=1)
        self.assertTrue(event)

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
