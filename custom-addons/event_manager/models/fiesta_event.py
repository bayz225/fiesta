from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime


class FiestaEvent(models.Model):
    _name = 'fiesta.event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Un événement'
    _order = 'create_date desc, id desc'

    name = fields.Char(string="Nom de l'événement", required=True, tracking=True)
    description = fields.Text(string='Description')
    contact_id = fields.Many2one(
        'res.partner',
        string='Organisateur',
        required=True,
        default=lambda self: self.env.user.partner_id,
        tracking=True,
    )
    date = fields.Date(string='Date', required=True, tracking=True)
    time = fields.Float(string="Heure", tracking=True)
    location = fields.Char(string="Lieu", required=True, default="À définir", tracking=True)
    party_theme = fields.Integer(string='Thème', required=True, default=1)
    max_guest = fields.Integer(string="Nombre max d'invités", default=10, tracking=True)
    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('confirmed', 'Confirmé'),
            ('done', 'Terminé'),
            ('cancelled', 'Annulé'),
        ],
        string='Statut',
        default='draft',
        required=True,
        tracking=True,
    )
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

    is_done = fields.Boolean(
        string='Terminé',
        compute='_compute_is_done',
    )
    can_add_guest = fields.Boolean(
        string='Peut ajouter des invités',
        compute='_compute_can_add_guest',
    )
    

    is_owner = fields.Boolean(
        string='Est propriétaire',
        compute='_compute_is_owner',
    )
    is_manager = fields.Boolean(
        string='Est manager',
        compute='_compute_is_manager',
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
    
    @api.depends('date')
    def _compute_is_done(self):
        deadline_days = int(self.env['ir.config_parameter'].sudo().get_param('event_manager.confirmation_days', 5))
        today = fields.Date.today()
        for event in self:
            if event.date:
                event.is_done = (event.date - datetime.timedelta(days=deadline_days)) <= today
            else:
                event.is_done = False

    @api.depends('total_guest', 'max_guest')
    def _compute_can_add_guest(self):
        today = fields.Date.today()
        for event in self:
            if event.max_guest:
                event.can_add_guest = event.total_guest < event.max_guest
            else:
                event.can_add_guest = False

    @api.depends('contact_id')
    def _compute_is_owner(self):
        for event in self:
            event.is_owner = event.contact_id == self.env.user.partner_id 

    @api.depends('contact_id')
    def _compute_is_manager(self):
        for event in self:
            event.is_manager = self.env.user.has_group('event_manager.group_event_manager')

    def action_confirm(self):
        today = fields.Date.today()
        for event in self:
            if not event.is_owner and not event.is_manager:
                raise ValidationError("Vous n'avez pas le droit de confirmer cet événement.")
            if event.date < today:
                raise ValidationError("L'événement ne peut plus être confirmé car sa date est dépassée.")
            if event.state != 'draft':
                raise ValidationError("L'événement doit être à l'état 'Brouillon' pour être confirmé.")

        self.write({'state': 'confirmed'})

    def action_done(self):
        today = fields.Date.today()
        for event in self:
            if not event.is_owner and not event.is_manager:
                raise ValidationError("Vous n'avez pas le droit de terminer cet événement.")
            if event.state != 'confirmed':
                raise ValidationError("L'événement doit être à l'état 'Confirmé' pour être terminé.")
            if event.date > today:
                raise ValidationError("L'événement n'est pas encore terminé.")

        self.write({'state': 'done'})

    def action_cancel(self):
        today = fields.Date.today()
        for event in self:
            if not event.is_owner and not event.is_manager:
                raise ValidationError("Vous n'avez pas le droit d'annuler cet événement.")
            if event.date < today:
                raise ValidationError("L'événement ne peut pas être annulé.")
            if event.state == 'done' or event.state == 'cancelled':
                raise ValidationError("L'événement doit être à l'état de 'brouillons' ou 'Confirmé' pour être annulé.")
        
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        for event in self:
            if not event.is_owner and not event.is_manager:
                raise ValidationError("Vous n'avez pas le droit de réinitialiser cet événement.")
            if event.state != "cancelled":
                raise ValidationError("L'événement doit être à l'état 'Annulé' pour être réinitialisé.")
        
        self.write({'state': 'draft'})