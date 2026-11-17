import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError


def _format_float_time(value):
    hours = int(value)
    minutes = int(round((value - hours) * 60))
    if minutes == 60:
        hours += 1
        minutes = 0
    return f"{hours:02d}h{minutes:02d}"

class FiestaEventInvitation(models.Model):
    _name = 'fiesta.event.invitation'
    _description = 'Invitation à un événement'
    _order = 'create_date desc, id desc'

    _fiesta_event_guest_unique = models.Constraint(
        "UNIQUE(event_id, guest_id)",
        "Un contact ne peut être invité qu'une seule fois à un même événement."
    )

    event_id = fields.Many2one(
        'fiesta.event',
        string='Événement',
        required=True,
        ondelete='cascade'
    )
    guest_id = fields.Many2one(
        'res.partner',
        string='Invité',
        required=True,
        ondelete='cascade'
    )
    arrival_time = fields.Float(
        string="Heure d'arrivée",
        default=False
    )
    number_of_companions = fields.Integer(
        string="Nombre d'accompagnants",
        default=0
    )
    available_places_char = fields.Char(
        string="Places disponibles",
        related='event_id.available_places_char',
        readonly=True,
    )
    available_places_int = fields.Integer(
        string="Nombre de places disponibles",
        related='event_id.available_places_int',
        readonly=True,
    )
    max_guest = fields.Integer(
        string="Nombre max d'invités",
        related='event_id.max_guest',
        readonly=True,
    )
    event_name = fields.Char(
        related='event_id.name',
        string='Nom de l\'événement',
        readonly=True,
    )
    event_date = fields.Date(
        related='event_id.date',
        string='Date de l\'événement',
        readonly=True,
    )
    event_time = fields.Float(
        related='event_id.time',
        string='Heure de l\'événement',
        readonly=True,
    )
    event_location = fields.Char(
        related='event_id.location',
        string='Lieu de l\'événement',
        readonly=True,
    )
    contact_id = fields.Many2one(
        'res.partner',
        string='Organisateur',
        related='event_id.contact_id',
        readonly=True,
    )
    is_expired_confirmation = fields.Boolean(
        string="Confirmation expirée", 
        compute='_compute_is_expired_confirmation',
    )

    def _compute_is_expired_confirmation(self):
        deadline_days = int(self.env['ir.config_parameter'].sudo().get_param('event_manager.confirmation_days', 5))
        today = fields.Date.today()
        for line in self:
            if not line.event_date:
                line.is_expired_confirmation = False
                continue
            expired_date = line.event_date - datetime.timedelta(days=deadline_days)
            line.is_expired_confirmation = bool(expired_date <= today)

    @api.constrains('event_id', 'guest_id', 'arrival_time', 'number_of_companions')
    def _check_confirmation_deadline(self):
        for line in self:
            if not line.event_id:
                continue
            if line.event_id.state in ('cancelled', 'done'):
                raise ValidationError(
                    "Impossible d'ajouter ou de modifier une invitation pour un événement annulé ou terminé."
                )
            if line.is_expired_confirmation:
                raise ValidationError(
                    "La date limite de confirmation de présence est dépassée. "
                    "Vous ne pouvez plus ajouter ou modifier les informations."
                )

    @api.constrains('event_id', 'guest_id')
    def _check_guest_validity(self):
        # 1. Vérification au sein du lot en cours (intra-batch)
        batch_pairs = set()
        for line in self:
            if not line.event_id or not line.guest_id:
                continue

            pair = (line.event_id.id, line.guest_id.id)
            if pair in batch_pairs:
                raise ValidationError(
                    f"Le contact {line.guest_id.name} est spécifié en double dans cette opération !"
                )
            batch_pairs.add(pair)

            # 2. Vérification contre les enregistrements existants en base
            domain = [
                ('event_id', '=', line.event_id.id),
                ('guest_id', '=', line.guest_id.id),
                ('id', '!=', line.id),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(
                    f"Le contact {line.guest_id.name} est déjà inscrit comme invité à cet événement !"
                )

    @api.constrains('number_of_companions', 'event_id')
    def _check_number_of_companions(self):
        for line in self:
            if line.number_of_companions < 0:
                raise ValidationError(
                    "Le nombre d'accompagnants ne peut pas être négatif."
                )

            if line.event_id and line.event_id.total_guest > line.event_id.max_guest:
                max_allowed_companions = line.event_id.max_guest - (
                    line.event_id.total_guest - line.number_of_companions
                )
                raise ValidationError(
                    f"Vous ne pouvez pas ajouter {line.number_of_companions} accompagnant(s). "
                    f"Nombre maximum d'accompagnants autorisés pour cette invitation : {max(0, max_allowed_companions)}."
                )

    @api.constrains('arrival_time', 'event_id')
    def _check_arrival_time(self):
        time_buf = int(self.env['ir.config_parameter'].sudo().get_param('event_manager.arrival_time_buffer', 2))
        for line in self:
            if line.arrival_time and line.event_id:
                min_time = line.event_id.time - time_buf
                max_time = line.event_id.time + time_buf
                if line.arrival_time < min_time or line.arrival_time > max_time:
                    raise ValidationError(
                        f"L'heure d'arrivée doit être comprise entre "
                        f"{_format_float_time(min_time)} et {_format_float_time(max_time)}."
                    )
