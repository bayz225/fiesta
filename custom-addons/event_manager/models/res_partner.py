from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    events_organized_ids = fields.One2many(
        'fiesta.event', 
        'contact_id', 
        string="Événements organisés",
    )
    invitation_ids = fields.One2many(
        'fiesta.event.invitation',
        'guest_id',
        string="Invitations reçues"
    )
    event_list = fields.Many2many(
        'fiesta.event',
        compute='_compute_event_list',
        string="Tous les événements",
        store=True,
    )
    event_count = fields.Integer(
        string='Nombre d\'événements',
        compute='_compute_event_stats',
        store=True,
    )
    total_guests_count = fields.Integer(
        string='Nombre total d\'invités',
        compute='_compute_event_stats',
        store=True,
    )
    
    @api.depends('invitation_ids', 'invitation_ids.event_id', 'invitation_ids.number_of_companions', 'invitation_ids.event_id.total_guest')
    def _compute_event_stats(self):
        for partner in self:
            events = partner.invitation_ids.mapped('event_id')
            partner.event_count = len(events)
            partner.total_guests_count = sum(events.mapped('total_guest')) if events else 0

    @api.depends('events_organized_ids', 'invitation_ids')
    def _compute_event_list(self):
        for partner in self:
            partner.event_list = partner.events_organized_ids | partner.invitation_ids.mapped('event_id')
