# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models,fields,api
from datetime import timedelta
from odoo.exceptions import ValidationError
import re

class RecurringSubscriptionCredit(models.Model):
    _name = 'recurring.subscription.credit'
    _description = 'Recurring Subscription Credit'
    _rec_name = 'recurring_subscription_id'
    _inherit = ['mail.thread','mail.activity.mixin']


    recurring_subscription_id = fields.Many2one('recurring.subscription',string='Recurring Subscription'
                                                ,required=True)
    partner_id = fields.Many2one('res.partner',string='Customer',
                                 related='recurring_subscription_id.customer_id')
    company_id = fields.Many2one('res.company',string='Company',
                                 related='recurring_subscription_id.company_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.ref('base.USD')
    )
    subscription_amount = fields.Monetary(string='Subscription Amount'
                                          ,related='recurring_subscription_id.recurring_amount')

    credit_amount = fields.Monetary(string='Credit Amount',default=1)
    establishment_id = fields.Char(string='Establishment ID',related='recurring_subscription_id.establishment_id')
    due_date = fields.Date(string='Due Date',related='recurring_subscription_id.due_date',store=True)
    state = fields.Selection(selection=[('pending','Pending'),('confirmed','Confirmed'),
                                        ('first_approved','First Approved'),('fully_approved','Fully Approved'),
                                        ('rejected','Rejected'),],string='State',default='pending',tracking=True)
    period_date = fields.Date(string='Period Date')
    is_valid_period = fields.Boolean(
        compute='_compute_is_valid_period',
        store=True
    )

    @api.depends('period_date', 'due_date')
    def _compute_is_valid_period(self):
        """used to validate the validity of the period date"""
        for record in self:
            if record.period_date and record.due_date:
                record.is_valid_period = record.period_date < record.due_date
            else:
                record.is_valid_period = False


    @api.onchange('credit_amount')
    def _onchange_credit_amount(self):
        """used to validate the credit amount"""
        if self.recurring_subscription_id:
            subscription_amount = self.recurring_subscription_id.recurring_amount
            if self.credit_amount == 0 or self.credit_amount > subscription_amount:
                self.recurring_subscription_id = None