from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AddContactToEventWizard(models.TransientModel):
    _name = "add.contact.to.event.wizard"
    _description = "Assistant d'ajout d'invités à un événement"

    event_id = fields.Many2one(
        'fiesta.event',
        string='Événement',
        required=True
    )
    excluded_guest_ids = fields.Many2many(
        'res.partner',
        compute='_compute_excluded_guest_ids',
        string='Invités exclus'
    )
    line_ids = fields.One2many(
        'add.contact.to.event.wizard.line',
        'wizard_id',
        string="Liste des invités à ajouter"
    )

    @api.model
    def default_get(self, fields):
        res = super(AddContactToEventWizard, self).default_get(fields)
        if 'event_id' in fields and 'event_id' not in res:
            if 'active_id' in self.env.context:
                res['event_id'] = self.env.context['active_id']
        return res

    # Filtrer les invités existants, déjà sélectionnés et l'organisateur de l'événement
    @api.depends('event_id', 'event_id.invitation_line_ids.guest_id', 'event_id.contact_id', 'line_ids.guest_id')
    def _compute_excluded_guest_ids(self):
        for wizard in self:
            if not wizard.event_id:
                wizard.excluded_guest_ids = self.env['res.partner']
                continue

            # Contacts déjà invités + organisateur + lignes en cours
            excluded_partners = wizard.event_id.invitation_line_ids.mapped('guest_id')
            if wizard.event_id.contact_id:
                excluded_partners |= wizard.event_id.contact_id
            excluded_partners |= wizard.line_ids.mapped('guest_id')

            wizard.excluded_guest_ids = excluded_partners

    def action_add_contacts(self):
        self.ensure_one()

        if not self.line_ids:
            raise ValidationError(
                'Veuillez ajouter au moins un invité.'
            )

        if self.event_id.available_places_int < len(self.line_ids):
            raise ValidationError(
                f"Vous ne pouvez pas ajouter ({len(self.line_ids)}) invités. "
                f"Le nombre de places disponibles est de {self.event_id.available_places_int}."
            )
        
        invitation_vals = [
            {
                'event_id': self.event_id.id,
                'guest_id': line.guest_id.id,
            }
            for line in self.line_ids
        ]
        self.env['fiesta.event.invitation'].create(invitation_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'soft_reload',
        }


class AddContactToEventWizardLine(models.TransientModel):
    _name = "add.contact.to.event.wizard.line"
    _description = "Ligne d'assistant d'ajout d'invité"

    wizard_id = fields.Many2one(
        'add.contact.to.event.wizard',
        string='Assistant',
        ondelete='cascade'
    )
    guest_id = fields.Many2one(
        'res.partner',
        string='Invité',
        required=True,
        domain="[('is_company', '=', False), ('id', 'not in', parent.excluded_guest_ids)]"
    )