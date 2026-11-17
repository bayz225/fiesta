from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api

class FiestaEventDashboard(models.AbstractModel):
    _name = 'fiesta.event.dashboard'
    _description = 'Tableau de bord des événements'

    @api.model
    def get_tiles_data(self):
        today = fields.Date.context_today(self)
        first_day_current_month = today.replace(day=1)
        last_day_current_month = first_day_current_month + relativedelta(months=1) - timedelta(days=1)
        first_day_last_month = first_day_current_month - relativedelta(months=1)
        seven_days_ago = today - timedelta(days=7)
        same_day_last_month = today - relativedelta(months=1)

        Event = self.env["fiesta.event"]

        # 1. Statistiques globales (Cartes)
        count_all_events = Event.search_count([])
        count_events_created_last_7_days = Event.search_count([("create_date", ">=", seven_days_ago)])
        count_fully_booked_events = Event.search_count([("available_places_int", "=", 0)])
        
        # Exclut les événements annulés sur l'ensemble du mois en cours et du mois précédent
        count_events_of_this_month = Event.search_count([
            ("date", ">=", first_day_current_month),
            ("date", "<=", last_day_current_month),
            ("state", "!=", "cancelled"),
        ])

        count_events_of_last_month = Event.search_count([
            ("date", ">=", first_day_last_month),
            ("date", "<", first_day_current_month),
            ("state", "!=", "cancelled"),
        ])

        # Événements à venir du mois en cours uniquement (hors événements annulés)
        count_upcoming_events = Event.search_count([
            ("date", ">=", today),
            ("date", "<=", last_day_current_month),
            ("state", "!=", "cancelled"),
        ])

        # 2. Liste des 10 derniers événements
        list_of_10_last_created_events = Event.search([], order="create_date desc", limit=10)

        # 3. Calcul sécurisé des pourcentages
        percentage_of_created_events_last_7_days = round(100 * count_events_created_last_7_days / count_all_events, 1) if count_all_events > 0 else 0.0
        percentage_of_events_fully_booked = round(100 * count_fully_booked_events / count_all_events, 1) if count_all_events > 0 else 0.0
        
        percentage_of_events_this_month = 0.0
        if count_events_of_last_month > 0:
            percentage_of_events_this_month = round(((count_events_of_this_month - count_events_of_last_month) / count_events_of_last_month) * 100, 1)
        elif count_events_of_this_month > 0:
            percentage_of_events_this_month = 100.0

        # 4. Évolution sur 6 mois (Graphique) - Optimisé avec _read_group (Odoo 19)
        six_months_ago = first_day_current_month - relativedelta(months=5)

        grouped_data = Event._read_group(
            domain=[
                ('date', '>=', six_months_ago),
                ('date', '<', first_day_current_month + relativedelta(months=1)),
                ('state', '!=', 'cancelled'),
            ],
            groupby=['date:month'],
            aggregates=['__count', 'total_guest:sum'],
        )
        data_by_month = {
            month_date: (count, guest_sum or 0)
            for month_date, count, guest_sum in grouped_data
            if month_date
        }

        month_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
        chart_labels = []
        chart_values = []
        monthly_stats = []

        # Construction des 6 mois (même si vides)
        for i in range(5, -1, -1):
            m_start = first_day_current_month - relativedelta(months=i)
            label = f"{month_names[m_start.month - 1]} {m_start.year}"
            count, guest_count = data_by_month.get(m_start, (0, 0))

            chart_labels.append(label)
            chart_values.append(count)
            monthly_stats.append({
                "label": label,
                "count": count,
                "guest_count": guest_count,
            })

        # Sécurisation des valeurs max/min au cas où tout est à zéro
        max_period = max(monthly_stats, key=lambda x: x["count"]) if monthly_stats else {}
        min_period = min(monthly_stats, key=lambda x: x["count"]) if monthly_stats else {}
        max_guest_period = max(monthly_stats, key=lambda x: x["guest_count"]) if monthly_stats else {}

        # 5. Formatage du retour JSON
        return {
            "count_all_events": count_all_events,
            "percentage_of_created_events_last_7_days": percentage_of_created_events_last_7_days,
            "count_upcoming_events": count_upcoming_events,
            "count_events_of_this_month": count_events_of_this_month,
            "percentage_of_events_this_month": percentage_of_events_this_month,
            "percentage_of_events_fully_booked": percentage_of_events_fully_booked,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
            "max_period": max_period,
            "min_period": min_period,
            "max_guest_period": max_guest_period,
            "list_of_last_created_events": [
                {
                    'id': event.id,
                    'name': event.name,
                    'organizer': [event.contact_id.id, event.contact_id.name] if event.contact_id else False,
                    # Formatage des dates géré en Python pour simplifier le composant OWL
                    'date': event.date.strftime("%d/%m/%Y") if event.date else "",
                    'location': event.location,
                    "available_places_percentage": round((event.available_places_int * 100 / event.max_guest if event.max_guest else 0), 1),
                } for event in list_of_10_last_created_events
            ]
        }