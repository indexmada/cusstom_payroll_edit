# -*- coding: utf-8 -*-

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    work_entry_input_ids = fields.One2many(
        string="Work entry input",
        comodel_name="saisie.work.entry",
        inverse_name="employee_id")

    other_entry_input_ids = fields.One2many(
        string="Other entry input",
        comodel_name="saisie.other.entry",
        inverse_name="employee_id")
