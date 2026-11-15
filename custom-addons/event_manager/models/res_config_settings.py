from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    confirmation_days = fields.Integer(
        string="Date limite de confirmation de présence (jours)",
        config_parameter='event_manager.confirmation_days',
        default=5
    )
    arrival_time_buffer = fields.Integer(
        string="Marge d'heure d'arrivée (heures)",
        config_parameter='event_manager.arrival_time_buffer',
        default=2
    )
