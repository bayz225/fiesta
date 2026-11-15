from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError

class AddGuestInfoToEventWizard(models.TransientModel):
    _name = "add.guest.info.to.event.wizard"
    _description = "Ajouter les informations d'arrivés d'un invité (Wizard)"

    event_id = fields.Many2one(
        'fiesta.event',
        string='Événement',
        required=True,
        readonly=True
    )
    guest_id = fields.Many2one(
        'res.partner',
        string='Invité',
        required=True,
        readonly=True
    )
    arrival_time = fields.Float(
        string="Heure",
    )
    number_of_companions = fields.Integer(string='Nombre d\'accompagnants')

    @api.model
    def default_get(self, fields):
        res = super(AddGuestInfoToEventWizard, self).default_get(fields)

        guest_id = self.env.context.get('default_guest_id')
        event_id = self.env.context.get('default_event_id')

        if guest_id and 'guest_id' in fields:
            res['guest_id'] = guest_id

        if event_id and 'event_id' in fields:
            res['event_id'] = event_id

        return res

    @api.onchange('event_id', 'guest_id')
    def _onchange_guest_info(self):
        for wizard in self:
            if wizard.event_id and wizard.guest_id:
                guest_line = wizard.event_id.invitation_line_ids.filtered(
                    lambda line: line.guest_id == wizard.guest_id
                )
                if guest_line:
                    is_updated = True if guest_line[0].write_date != guest_line[0].create_date else False
                    if is_updated:
                        wizard.arrival_time = guest_line[0].arrival_time
                        wizard.number_of_companions = guest_line[0].number_of_companions
                    else:
                        wizard.arrival_time = wizard.event_id.time

    def action_add_guest_info(self):
        self.ensure_one()
        
        if self.number_of_companions and self.number_of_companions < 0:
            raise ValidationError(
                _("Le nombre d'accompagnants ne peut pas être négatif.")
            ) 

        exist_line = self.event_id.invitation_line_ids.filtered(
            lambda line: line.guest_id == self.guest_id
        )

        if not exist_line and self.number_of_companions > self.event_id.available_places_int:
            raise ValidationError(
                _("Vous ne pouvez pas ajouter (%s) compagnons. Le nombre de place disponible est de %s.")
                % (self.number_of_companions, self.event_id.available_places_int)
            )

        if exist_line:
            new_available_places = self.event_id.available_places_int + exist_line.number_of_companions

            if new_available_places < self.number_of_companions:
                raise ValidationError(
                    _("Vous ne pouvez pas modifier le nombre de compagnons à (%s). Le nombre de place disponible est de %s.")
                    % (self.number_of_companions, new_available_places)
                )
            exist_line.write({
                'arrival_time': self.arrival_time,
                'number_of_companions': self.number_of_companions,
            })
        else:
            self.env['fiesta.event.invitation'].create({
                'event_id': self.event_id.id,
                'guest_id': self.guest_id.id,
                'arrival_time': self.arrival_time,
                'number_of_companions': self.number_of_companions,
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'soft_reload',
        }