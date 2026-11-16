from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FiestaEvent(models.Model):
    _name = 'fiesta.event'
    _description = 'Un événement'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Nom de l\'événement', required=True)
    description = fields.Text(string='Description')
    contact_id = fields.Many2one('res.partner', string='Organisateur', required=True)
    date = fields.Date(string='Date', required=True)
    time = fields.Float(string="Heure")
    location = fields.Char(string="Lieu", required=True, default="À définir")
    party_theme = fields.Integer(string='Thème', required=True)
    max_guest = fields.Integer(string='Nombre max d\'invités', default=10)
    invitation_line_ids = fields.One2many(
        'fiesta.event.invitation',
        'event_id',
        string='Invitations'
    )
    guest_ids = fields.Many2many(
        'res.partner',
        string='Invités',
        compute='_compute_guest_ids',
        store=True
    )
    total_guest = fields.Integer(
        string='Nombre total d\'invités',
        compute='_compute_total_guest',
        store=True,
    )
    available_places_char = fields.Char(
        string='Places disponibles (Texte)',
        compute='_compute_available_places',
        store=True
    )
    available_places_int = fields.Integer(
        string='Places disponibles',
        compute='_compute_available_places',
        store=True
    )

    @api.constrains('date', 'time')
    def _check_event_date(self):
        for event in self:
            if event.date and event.date < fields.Date.today():
                raise ValidationError("La date de l'événement ne peut pas être dans le passé.")
            if event.time < 0.0 or event.time >= 24.0:
                raise ValidationError("L'heure de l'événement doit être comprise entre 00:00 et 23:59.")

    @api.constrains('max_guest')
    def _check_max_guest(self):
        for event in self:
            if event.max_guest < 4:
                raise ValidationError("Le nombre maximum d'invités doit être supérieur ou égal à 4.")

    @api.constrains('location')
    def _check_location(self):
        for event in self:
            if not event.location:
                raise ValidationError("Le lieu de l'événement est requis.")
                
    @api.depends('invitation_line_ids.guest_id')
    def _compute_guest_ids(self):
        for event in self:
            event.guest_ids = event.invitation_line_ids.mapped('guest_id')

    # Compter le nombre total d'invités
    @api.depends(
        'invitation_line_ids',
        'invitation_line_ids.number_of_companions'
    )
    def _compute_total_guest(self):
        for event in self:
            event.total_guest = sum(
                1 + line.number_of_companions for line in event.invitation_line_ids
            )
    
    @api.depends('total_guest', 'max_guest')
    def _compute_available_places(self):
        for event in self:
            places = event.max_guest - event.total_guest
            event.available_places_char = f"{places} / {event.max_guest}"
            event.available_places_int = places
