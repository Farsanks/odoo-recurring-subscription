# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import re

class PartnerAccountId(models.Model):
    _name = 'partner.account.id'
    _description = 'Partner Account ID'
    _rec_name = 'account_id'

    account_id = fields.Char(string='Account ID',required=True,readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner',string='Customer', ondelete='cascade',readonly=True)
    _unique_account_id = models.Constraint('UNIQUE(account_id)','Account ID must be unique')

    @api.constrains('account_id')
    def _check_account_id(self):
        """Validate account ID which contains 3 letters,3 numbers,2 special characters and must be unique"""
        for record in self:
            if record.account_id:
                pattern = r'^(?=(?:.*[A-Za-z]){3})(?=(?:.*\d){3})(?=(?:.*[^A-Za-z\d]){2}).{8}$'
                if not re.match(pattern, record.account_id):
                    raise ValidationError('Account ID must be unique')