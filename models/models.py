# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class custom_payroll_edit(models.Model):
#     _name = 'custom_payroll_edit.custom_payroll_edit'
#     _description = 'custom_payroll_edit.custom_payroll_edit'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
