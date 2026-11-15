from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime

class FiestaEventInvitation(models.Model):
    _name = 'fiesta.event.invitation'
    _description = 'Invitation à un événement'
    _order = 'create_date desc, id desc'

    _sql_constraints = [
        (
            'unique_event_guest',
            'UNIQUE(event_id, guest_id)',
            "Ce contact est déjà inscrit comme invité à cet événement !",
        )
    ]

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
        string="Places disponibles int",
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
        for line in self:
            expired_date = line.event_date - datetime.timedelta(days=deadline_days)
            line.is_expired_confirmation = bool(expired_date <= datetime.date.today())

    @api.constrains('event_id', 'guest_id')
    def _check_guest_validity(self):
        # 1. Vérification au sein du lot en cours (intra-batch)
        batch_pairs = set()
        for line in self:
            if not line.event_id or not line.guest_id:
                continue
            
            if line.is_expired_confirmation:
                raise ValidationError(
                    _("La date limite de confirmation de présence est dépassée. Vous ne pouvez plus ajouter ou modifier les informations.")
                )

            pair = (line.event_id.id, line.guest_id.id)
            if pair in batch_pairs:
                raise ValidationError(
                        _(
                            "Le contact %(guest)s est spécifié en double dans cette opération !",
                            guest=line.guest_id.name,
                        )
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
                    _(
                        "Le contact %(guest)s est déjà inscrit comme invité à cet événement !",
                        guest=line.guest_id.name,
                    )
                )

    @api.constrains('number_of_companions', 'event_id')
    def _check_number_of_companions(self):
        for line in self:
            if line.number_of_companions < 0:
                raise ValidationError(
                    _("Le nombre d'accompagnants ne peut pas être négatif.")
                )

            if line.event_id:
                if line.event_id.total_guest > line.event_id.max_guest:
                    max_allowed_companions = line.event_id.max_guest - (
                        line.event_id.total_guest - line.number_of_companions
                    )
                    raise ValidationError(
                        _(
                            "Vous ne pouvez pas ajouter %s accompagnant(s). "
                            "Nombre maximum d'accompagnants autorisés pour cette invitation : %s."
                        ) % (line.number_of_companions, max(0, max_allowed_companions))
                    )
    
    @api.constrains('arrival_time', 'event_id')
    def _check_arrival_time(self):
        time_buf = int(self.env['ir.config_parameter'].sudo().get_param('event_manager.arrival_time_buffer', 2))
        for line in self:
            if line.arrival_time and line.event_id:
                if line.arrival_time < line.event_id.time - time_buf or line.arrival_time > line.event_id.time + time_buf:
                    raise ValidationError(
                        _("L'heure d'arrivée doit être comprise entre %sH et %sH.")
                        % (int(line.event_id.time - time_buf), int(line.event_id.time + time_buf))
                    )
