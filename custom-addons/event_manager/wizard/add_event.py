from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AddEventWizard(models.TransientModel):
    _name = "add.event.wizard"
    _description = "Créer un événement"

    name = fields.Char(string="Nom de l'événement", required=True)
    description = fields.Text(string='Description')
    contact_id = fields.Many2one(
        'res.partner',
        string='Organisateur',
        required=True
    )
    date = fields.Date(string="Date de l'événement", required=True)
    time = fields.Float(string="Heure")
    location = fields.Char(string='Lieu')
    party_theme = fields.Integer(string='Thème', required=True)
    max_guest = fields.Integer(string="Nombre max d'invités", default=10)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') == 'res.partner' and self.env.context.get('active_id'):
            res['contact_id'] = self.env.context.get('active_id')
        return res

    @api.constrains('date')
    def _check_event_date(self):
        for wizard in self:
            if wizard.date and wizard.date < fields.Date.today():
                raise ValidationError(_("La date de l'événement ne peut pas être dans le passé."))

    @api.constrains('max_guest')
    def _check_max_guest(self):
        for wizard in self:
            if wizard.max_guest < 4:
                raise ValidationError(_("Le nombre maximum d'invités doit être supérieur à 4."))

    def action_add_event(self):
        self.ensure_one()

        event_vals = {
            'name': self.name,
            'description': self.description,
            'contact_id': self.contact_id.id,
            'date': self.date,
            'time': self.time,
            'location': self.location,
            'party_theme': self.party_theme,
            'max_guest': self.max_guest,
        }

        event = self.env['fiesta.event'].create(event_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'soft_reload',
        }