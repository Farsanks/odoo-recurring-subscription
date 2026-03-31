# -*- coding: utf-8 -*-

from email.policy import default

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.orm.decorators import ondelete


class BillingSchedule(models.Model):
    _name = 'billing.schedule'
    _description = 'Billing Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'


    name = fields.Char(string='Name')
    simulation = fields.Boolean(string='Simulation', tracking=True)
    period = fields.Date(string='Period', tracking=True)
    restrict_customer_ids = fields.Many2many('res.partner', string='Restrict Customers',
                                             tracking=True, compute='_compute_restrict_customer_ids', store=True)
    active = fields.Boolean(string='Active', default=True)
    recurring_subscription_ids = fields.Many2many('recurring.subscription',
                                                  string='Recurring Subscriptions', tracking=True)
    total_credit_amount = fields.Monetary(string='Total Credit Amount', compute='_compute_total_credit_amount',
                                          store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.ref('base.USD'))
    recurring_subscription_id = fields.Many2one('recurring.subscription', string='Recurring Subscription')
    recurring_subscription_count = fields.Integer(string='Subscriptions'
                                                  , compute='_compute_recurring_subscription_count')
    credit_ids = fields.Many2many('recurring.subscription.credit'
                                  , string='Credits', compute='_compute_credit_ids', store=False)

    @api.depends('recurring_subscription_ids')
    def _compute_recurring_subscription_count(self):
        """used to compute the subscription count"""
        for record in self:
            record.update({'recurring_subscription_count': len(record.recurring_subscription_ids)})

    def action_view_recurring_subscriptions(self):
        """open the linked subscriptions"""
        self.ensure_one()
        return {
            'name': 'Recurring Subscriptions',
            'type': 'ir.actions.act_window',
            'res_model': 'recurring.subscription',
            'view_mode': 'list',
            'res_id': self.recurring_subscription_ids,
            'domain': [('id', 'in', self.recurring_subscription_ids.ids)],
        }

    @api.depends('recurring_subscription_ids')
    def _compute_restrict_customer_ids(self):
        for record in self:
            if record.recurring_subscription_ids:
                customer_ids = record.recurring_subscription_ids.mapped('partner_id').ids
                record.update({'restrict_customer_ids': customer_ids})
            else:
                record.update({'restrict_customer_ids': [(5, 0, 0)]})

    @api.depends('recurring_subscription_ids')
    def _compute_credit_ids(self):
        """used to compute the credit amount"""
        for record in self:
            if record.recurring_subscription_ids:
                credits = self.env['recurring.subscription.credit'].search([
                    ('recurring_subscription_id', 'in', record.recurring_subscription_ids.ids),
                    ('state', '=', 'confirmed')])
                record.update({'credit_ids': [fields.Command.set(credits.ids)]})
            else:
                record.update({'credit_ids': [fields.Command.clear()]})

    @api.depends('recurring_subscription_ids')
    def _compute_total_credit_amount(self):
        """used to compute the total credit amount"""
        for record in self:
            if record.recurring_subscription_ids:
                credits = (self.env['recurring.subscription.credit'].search
                           ([('recurring_subscription_id', 'in', record.recurring_subscription_ids.ids),
                             ('recurring_subscription_id.state', '=', 'confirm')]))
                record.update({
                    'total_credit_amount': sum(credits.mapped('credit_amount')),
                })
            else:
                record.update({'total_credit_amount': 0.0})

    def action_manual_billing(self):
        """used for creating the invoice"""
        self.ensure_one()
        credit_product = self.env['product.product'].search([('default_code','=','SubscriptionCredit')],limit=1)
        if not credit_product:
            raise UserError("Credit Product not found")
        for subscription in self.recurring_subscription_ids:
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': subscription.partner_id.id,
                'invoice_line_ids': [
                    fields.Command.create({
                        'product_id': subscription.product_id.id,
                        'quantity': 1,
                        'price_unit': subscription.recurring_amount,
                    })
                ]
            })

            credit = self.env['recurring.subscription.credit'].search(
                [('recurring_subscription_id', '=', subscription.id),
                 ('state', '=', 'confirmed'), ('credit_amount', '=', subscription.recurring_amount),],
                order='id asc', limit=1)

            if not credit:
                credit = self.env['recurring.subscription.credit'].search(
                    [('recurring_subscription_id', '=', subscription.id),
                     ('state', '=', 'confirmed'), ], order='id asc', limit=1)
            if credit:
                invoice.write({
                    'invoice_line_ids': [
                        fields.Command.create({
                            'product_id': credit_product.id,
                            'quantity': 1,
                            'price_unit': -credit.credit_amount,
                            'name': f'Credit Applied-{credit.recurring_subscription_id.name}'
                            f'(credit ID: {credit.id} | ' f'Amount:{credit.credit_amount} '
                                    f'| ' f'Created: {credit.create_date.strftime("%Y-%m-%d %H:%M:%S") 
                            if credit.create_date else ''})',
                        })
                    ]
                })
        self.write({"active": False})

    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')

    @api.depends('recurring_subscription_ids')
    def _compute_invoice_count(self):
        """used to compute the invoice count"""
        for record in self:
            invoices = self.env['account.move'].search([('partner_id', 'in',
                                                         record.recurring_subscription_ids.mapped('partner_id').ids),
                                                        ('move_type', '=', 'out_invoice')])
            record.update({'invoice_count': len(invoices)})

    def action_view_invoices(self):
        """used for seeing the invoices"""
        self.ensure_one()
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'in', self.recurring_subscription_ids.mapped('partner_id').ids),
                ('move_type', '=', 'out_invoice'),
            ],
        }
