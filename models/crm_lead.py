# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = "crm.lead"

    order_id = fields.Char(string="Order ID",required=True)

    _unique_order_id = models.Constraint('UNIQUE(order_id)','Order ID must be unique')