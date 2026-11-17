from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class AddGuestInfoToEventWizard(models.TransientModel):
    _name = "add.guest.info.to.event.wizard"
    _description = "Assistant d'informations d'arrivée d'un invité"

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
        readonly=True,
        default=lambda self: self.env.user.partner_id
    )
    arrival_time = fields.Float(
        string="Heure",
    )
    number_of_companions = fields.Integer(string='Nombre d\'accompagnants')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        event_id = res.get('event_id')
        guest_id = self.env.user.partner_id.id

        if event_id and guest_id:
            guest_line = self.env['fiesta.event.invitation'].search([
                ('event_id', '=', event_id),
                ('guest_id', '=', guest_id)
            ], limit=1)

            if guest_line:
                res['arrival_time'] = guest_line.arrival_time
                res['number_of_companions'] = guest_line.number_of_companions
            else:
                event = self.env['fiesta.event'].browse(event_id)
                res['arrival_time'] = event.time

        return res

    def action_add_guest_info(self):
        self.ensure_one()

        if self.event_id.state != "confirmed":
            raise UserError("Veuillez attendre la confirmation de l'événement.")

        if self.number_of_companions < 0:
            raise ValidationError("Le nombre d'accompagnants ne peut pas être négatif.")

        exist_line = self.env['fiesta.event.invitation'].search([
            ('event_id', '=', self.event_id.id),
            ('guest_id', '=', self.guest_id.id)
        ], limit=1)

        if not exist_line:
            # Vérification à la création
            total_requested = 1 + self.number_of_companions
            if total_requested > self.event_id.available_places_int:
                raise ValidationError(
                    f"Vous ne pouvez pas ajouter ({total_requested}) participant(s). "
                    f"Il ne reste que {self.event_id.available_places_int} place(s)."
                )
            
            self.env['fiesta.event.invitation'].create({
                'event_id': self.event_id.id,
                'guest_id': self.guest_id.id,
                'arrival_time': self.arrival_time,
                'number_of_companions': self.number_of_companions,
            })
        else:
            # Vérification à la modification
            new_available_places = self.event_id.available_places_int + exist_line.number_of_companions
            if new_available_places < self.number_of_companions:
                raise ValidationError(
                    f"Vous ne pouvez pas modifier le nombre d'accompagnants à ({self.number_of_companions}). "
                    f"Il ne reste que {new_available_places} place(s)."
                )
                
            exist_line.write({
                'arrival_time': self.arrival_time,
                'number_of_companions': self.number_of_companions,
            })

        return {
            'type': 'ir.actions.client',
            'tag': 'soft_reload',
        }
