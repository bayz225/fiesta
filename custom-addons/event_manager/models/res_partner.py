from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    events_organized_ids = fields.One2many(
        'fiesta.event', 
        'contact_id', 
        string="Événements organisés",
        # store=True
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
            partner.event_list = partner.invitation_ids.mapped('event_id')

    @api.model
    def get_tiles_data(self):
        today = fields.Date.today()
        first_day_current_month = today.replace(day=1)
        last_day_current_month = first_day_current_month + relativedelta(months=1) - timedelta(days=1)
        first_day_last_month = first_day_current_month - relativedelta(months=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        seven_days_ago = today - timedelta(days=7)
        same_day_last_month = first_day_current_month - relativedelta(months=1) + timedelta(days=today.day - 1)

        Event = self.env["fiesta.event"]

        # Total événements et mois passé
        all_events_count = Event.search_count([])
        events_created_last_7_days = Event.search([("create_date", ">=", seven_days_ago)])
        events_created_last_7_days_count = len(events_created_last_7_days)
        all_events_fully = Event.search_count([("available_places_int", "=", 0)])
        events_this_month = Event.search_count([
            ("date", ">=", first_day_current_month), 
            ("date", "<", today + timedelta(days=1))
        ])
        events_last_month = Event.search_count([
            ("date", ">=", first_day_last_month),
            ("date", "<", same_day_last_month + timedelta(days=1)),
        ])
        upcoming_events_count = Event.search_count([
            ("date", ">=", today), 
            ("date", "<", last_day_current_month + timedelta(days=1))
        ]) # Événements à partir d'aujourd'hui
        last_events_list = Event.search([], order="create_date desc", limit=10) # Derniers événements récents
        
        # Variation %
        all_events_last_week_percentage = round(100 * events_created_last_7_days_count / (all_events_count if all_events_count > 0 else 0), 1) # Pourcentage du total créé durant les 7 derniers jours
        all_events_fully_percentage = round(100 * all_events_fully / (all_events_count if all_events_count > 0 else 0), 1) # Pourcentage des événement remplis par rapport à tous les events
        this_month_events_percentage = 0
        if events_last_month > 0:
            this_month_events_percentage = round(((events_this_month - events_last_month) / events_last_month) * 100, 1)
        # Évolution sur 6 mois (Graphique & Analyse)
        month_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
        chart_labels = []
        chart_values = []
        monthly_stats = []
        for i in range(5, -1, -1):
            m_start = first_day_current_month - relativedelta(months=i)
            m_next = m_start + relativedelta(months=1)
            label = f"{month_names[m_start.month - 1]} {m_start.year}"
            events_of_month = Event.search([("date", ">=", m_start), ("date", "<", m_next)])
            count = len(events_of_month)
            guest_count = sum(events_of_month.mapped('total_guest'))
            chart_labels.append(label)
            chart_values.append(count)
            monthly_stats.append({"label": label, "count": count, "guest_count": guest_count})
        max_period = max(monthly_stats, key=lambda x: x["count"])
        min_period = min(monthly_stats, key=lambda x: x["count"])
        max_guest_period = max(monthly_stats, key=lambda x: x["guest_count"])
        return {
            "all_events_count": all_events_count,
            "all_events_last_week_percentage": all_events_last_week_percentage,
            "upcoming_events_count": upcoming_events_count,
            "this_month_events_count": events_this_month,
            "this_month_events_percentage": this_month_events_percentage,
            "all_events_fully_percentage": all_events_fully_percentage,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "max_period": max_period,
            "min_period": min_period,
            "max_guest_period": max_guest_period,
            "last_events_list": [
                {
                    'id': event.id,
                    'name': event.name,
                    'organizer': [event.contact_id.id, event.contact_id.name] if event.contact_id else False,
                    'date': event.date.strftime("%a %d %b %Y").title() if event.date else "",
                    'location': event.location,
                    "available_places_percentage": round((event.available_places_int * 100 / event.max_guest if event.max_guest else 0), 1),
                } for event in last_events_list
            ]
        }