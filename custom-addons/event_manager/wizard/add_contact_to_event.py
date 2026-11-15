from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError


class AddContactToEventWizard(models.TransientModel):
    _name = "add.contact.to.event.wizard"
    _description = "Ajouter des invités à un événement (Wizard)"

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

    #filtré les invités existants et l'organisateur de l'événement
    @api.depends('event_id', 'event_id.invitation_line_ids.guest_id', 'event_id.contact_id')
    def _compute_excluded_guest_ids(self):
        for wizard in self:
            if not wizard.event_id:
                wizard.excluded_guest_ids = self.env['res.partner']
                continue

            # Contacts déjà invités + organisateur
            excluded_partners = wizard.event_id.invitation_line_ids.mapped('guest_id')
            if wizard.event_id.contact_id:
                excluded_partners |= wizard.event_id.contact_id
                excluded_partners |= wizard.line_ids.mapped('guest_id')
            
            #filter les contact qui sont des entreprises
            is_company = self.env['res.partner'].search([('is_company', '=', True)])
            for company in is_company:
                excluded_partners |= company
            
            wizard.excluded_guest_ids = excluded_partners

    def action_add_contacts(self):
        self.ensure_one()

        if not self.line_ids:
            raise ValidationError(
                _('Veuillez ajouter au moins un invité.')
            )
        
        if self.event_id.available_places_int < len(self.line_ids):
            raise ValidationError(
                _("Vous ne pouvez pas ajouter (%s) invités. Le nombre de place disponible est de %s.")
                % (len(self.line_ids), self.event_id.available_places_int)
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
    _description = "Ligne d'ajout d'invité dans le wizard"

    wizard_id = fields.Many2one(
        'add.contact.to.event.wizard',
        string='Wizard',
        ondelete='cascade'
    )
    guest_id = fields.Many2one(
        'res.partner',
        string='Invité',
        required=True,
        domain="[('id', 'not in', parent.excluded_guest_ids)]"
    )