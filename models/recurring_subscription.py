# -*- coding: utf-8 -*-


from email.policy import default

from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import ValidationError
import re

class RecurringSubscription(models.Model):
    _name = 'recurring.subscription'
    _description = 'Recurring Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_id = fields.Char(string='Order ID', readonly=True, default='New')
    name = fields.Char(string='Name', required=True)
    establishment_id = fields.Char(string='Establishment ID', required=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    due_date = fields.Date(string='Due Date', default=fields.Date.today() + timedelta(days=15))
    next_billing = fields.Datetime(string='Next Billing')
    is_lead = fields.Boolean(string='Is Lead')
    customer_id = fields.Many2one('res.partner', string='Customer',required=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id, required=True)
    description = fields.Char(string='Description')
    terms_and_conditions = fields.Html(string='Terms and Conditions')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.ref('base.USD')
    )
    recurring_amount = fields.Monetary(string='Recurring Amount',default=1)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled'), ], string='State', default='draft', tracking=True)

    credit_ids = fields.One2many(
        'recurring.subscription.credit',
        'recurring_subscription_id', string='Subscription Credits',
        domain=[('is_valid_period', '=', True)]
    )
    billing_schedule_ids = fields.One2many(
        'billing.schedule', 'recurring_subscription_id', string='Billing Schedules',
    )
    billing_schedule_id = fields.Many2one('billing.schedule', string='Billing Schedule')

    _unique_name = models.Constraint(
        'UNIQUE(name)',
        'A Recurring Subscription with this name already exists!'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """used for setting the sequence number"""
        for vals in vals_list:
            if vals.get('order_id', 'New') == 'New':
                vals['order_id'] = self.env['ir.sequence'].next_by_code('recurring.subscription')

        return super().create(vals_list)


    def action_confirm(self):
        """used for setting the state to confirm"""
        self.write({'state': 'confirm'})

    def action_cancel(self):
        """used for setting the state to cancel"""
        self.write({'state': 'cancel'})

    @api.constrains('establishment_id')
    def _check_establishment_id(self):
        """used to validate the establishment id"""
        for record in self:
            if record.establishment_id:
                pattern = r'^(?=(?:.*[A-Za-z]){3})(?=(?:.*\d){3})(?=(?:.*[^A-Za-z\d]){2}).{8}$'
                if not re.match(pattern, record.establishment_id):
                    raise ValidationError(
                        "Establishment Id must contain 3 alphabets, 3 numbers and 2 special characters."
                    )

    @api.onchange('establishment_id')
    def _onchange_establishment_id(self):
        """Find partner by establishment id"""

        if self.establishment_id:
            partner = self.env['res.partner'].search([('establishment_id', '=', self.establishment_id)], limit=1)
            if partner:
                print(partner)
                self.write({'customer_id': partner.id})
            else:
                self.write({'customer_id': False})
                return {
                    'warning':{
                        'title':'No partner found',
                        'message':'No partner found',
                    }
                }


