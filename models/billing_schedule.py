# -*- coding: utf-8 -*-

from email.policy import default

from odoo import api, fields, models

class BillingSchedule(models.Model):
    _name = 'billing.schedule'
    _description = 'Billing Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name')
    simulation = fields.Boolean(string='Simulation',tracking=True)
    period = fields.Date(string='Period',tracking=True)
    restrict_customer_ids = fields.Many2many('res.partner',string='Restrict Customers',
                                             tracking=True,compute='_compute_restrict_customer_ids',store=True)
    active = fields.Boolean(string='Active')
    recurring_subscription_ids = fields.Many2many('recurring.subscription',
                                                  string='Recurring Subscriptions',tracking=True)
    total_credit_amount = fields.Monetary(string='Total Credit Amount',compute='_compute_total_credit_amount',store=True)
    currency_id = fields.Many2one('res.currency',string='Currency',
                                  default=lambda self: self.env.ref('base.USD'))
    recurring_subscription_id=fields.Many2one('recurring.subscription',string='Recurring Subscription')
    recurring_subscription_count = fields.Integer(string='Subscriptions'
                                                  ,compute='_compute_recurring_subscription_count')
    credit_ids = fields.Many2many('recurring.subscription.credit'
                                  ,string='Credits',compute='_compute_credit_ids',store=False)

    @api.depends('recurring_subscription_ids')
    def _compute_recurring_subscription_count(self):
        """used to compute the subscription count"""
        for record in self:
            record.update({'recurring_subscription_count' : len(record.recurring_subscription_ids)})


    def action_view_recurring_subscriptions(self):
        """open the linked subscriptions"""
        self.ensure_one()
        return {
            'name':'Recurring Subscriptions',
            'type':'ir.actions.act_window',
            'res_model':'recurring.subscription',
            'view_mode':'list',
            'res_id': self.recurring_subscription_ids,
            'domain':[('id','in', self.recurring_subscription_ids.ids)],
        }

    @api.depends('recurring_subscription_ids')
    def _compute_restrict_customer_ids(self):
        for record in self:
            if record.recurring_subscription_ids:
                customer_ids = record.recurring_subscription_ids.mapped('customer_id').ids
                record.update({'restrict_customer_ids':customer_ids})
            else:
                record.update({'restrict_customer_ids':[(5,0,0)]})

    @api.depends('recurring_subscription_ids')
    def _compute_credit_ids(self):
        """used to compute the credit amount"""
        for record in self:
            if record.recurring_subscription_ids:
                credits = self.env['recurring.subscription.credit'].search([('recurring_subscription_id','in',record.recurring_subscription_ids.ids),('state','=','confirmed')])
                record.update({'credit_ids':[fields.Command.set(credits.ids)]})
            else:
                record.update({'credit_ids':[fields.Command.clear()]})

    @api.depends('recurring_subscription_ids')
    def _compute_total_credit_amount(self):
        """used to compute the total credit amount"""
        for record in self:
            if record.recurring_subscription_ids:
                credits = (self.env['recurring.subscription.credit'].search
                           ([('recurring_subscription_id','in',record.recurring_subscription_ids.ids),('state','=','confirmed')]))
                record.update({
                    'total_credit_amount':sum(credits.mapped('credit_amount')),
                })
            else:
                record.update({'total_credit_amount':[(0,0)]})

