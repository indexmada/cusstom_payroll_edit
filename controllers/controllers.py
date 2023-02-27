# -*- coding: utf-8 -*-
# from odoo import http


# class CustomPayrollEdit(http.Controller):
#     @http.route('/custom_payroll_edit/custom_payroll_edit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_payroll_edit/custom_payroll_edit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_payroll_edit.listing', {
#             'root': '/custom_payroll_edit/custom_payroll_edit',
#             'objects': http.request.env['custom_payroll_edit.custom_payroll_edit'].search([]),
#         })

#     @http.route('/custom_payroll_edit/custom_payroll_edit/objects/<model("custom_payroll_edit.custom_payroll_edit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_payroll_edit.object', {
#             'object': obj
#         })
