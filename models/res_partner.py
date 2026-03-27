# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import re, string, random


class ResPartner(models.Model):
    _inherit = 'res.partner'

    establishment_id = fields.Char(string="Establishment ID")
    account_id = fields.Many2one(comodel_name='partner.account.id', string="Account ID", ondelete='cascade')

    _unique_establishment_id = models.Constraint('UNIQUE(establishment_id)',
                                                 'Establishment ID must be unique')

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

    # @api.model_create_multi
    # def create(self, vals_list):
    #     print(vals_list)
    #     """Auto create a unique Account ID for each partner"""
    #     records = super().create(vals_list)
    #     for record in records:
    #         account_id_value = self._generate_account_id()
    #         account = self.env['partner.account.id'].create({
    #             'account_id': account_id_value,
    #             'partner_id': record.id,
    #         })
    #         record.write({'account_id': account.id})
    #     return records

    def _generate_account_id(self):
        """Generate a unique Account ID for each partner"""
        letters = random.choices(string.ascii_uppercase, k=3)
        numbers = random.choices(string.digits, k=3)
        special = random.choices('@#$%', k=2)
        all_chars = letters + numbers + special
        random.shuffle(all_chars)
        return ''.join(all_chars)



