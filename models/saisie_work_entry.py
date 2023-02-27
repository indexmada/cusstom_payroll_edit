# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from odoo.tools import float_round, date_utils

MONTH_LIST = [
        ('janv', 'Janvier'),
        ('fev', 'Février'),
        ('mars', 'Mars'),
        ('avr', 'Avril'),
        ('mey','Mey'),
        ('juin', 'Juin'),
        ('jul', 'Juillet'),
        ('aout', 'Août'),
        ('sept', 'Septembre'),
        ('oct', 'Octobre'),
        ('nov', 'Novembre'),
        ('dec', 'Decembre')
    ]


class HrPayslipWorkedDayInherit(models.Model):
    _inherit = "hr.payslip.worked_days"

    saisie_work_entry_id = fields.Many2one("saisie.work.entry", string="Saisie Work Entry")
    imported = fields.Boolean("Is imported",default=False)

class HrPayslipInputInherit(models.Model):
    _inherit = "hr.payslip.input"

    saisie_other_entry = fields.Many2one("saisie.other.entry", string="Saisie Autre entrée")
    imported = fields.Boolean("Is imported",default=False)

class SaisieWorkEntry(models.Model):
    _name="saisie.work.entry"

    employee_id = fields.Many2one("hr.employee", string="Employé")
    matricule = fields.Char("Matricule")
    month = fields.Selection(MONTH_LIST, string="Mois de")
    work_entry_type = fields.Many2one("hr.work.entry.type",string="Rubrique")
    number_of_days = fields.Float("Nombre de jours")
    number_of_hours = fields.Float("Nombre d'Heures")
    year = fields.Char("Année")

    def update_worked_days_value(self):
        worked_day = self.env['hr.payslip.worked_days'].sudo().search([('saisie_work_entry_id','=', self.id)], limit=1)
        for rec in worked_day:
            rec.write({
                    'work_entry_type_id': self.work_entry_type.id,
                    'number_of_days': self.number_of_days,
                    'number_of_hours': self.number_of_hours,
                })

class SaisieOtherEntry(models.Model):
    _name="saisie.other.entry"

    employee_id = fields.Many2one("hr.employee", string="Employé")
    matricule = fields.Char("Matricule")
    month = fields.Selection(MONTH_LIST, string="Mois de")
    payslip_input_type = fields.Many2one("hr.payslip.input.type", string="Rubrique")
    amount = fields.Float("Montant")
    year = fields.Char("Année")

    def update_payslip_input_value(self):
        payslip_input_ids = self.env['hr.payslip.input'].sudo().search([('saisie_other_entry','=', self.id)])
        for input_id in payslip_input_ids:
            input_id.write({
                    'input_type_id': self.payslip_input_type.id,
                    'amount': self.amount,
                })

class HrPayslip(models.Model):
    _inherit="hr.payslip"

    # Préavis non Effectué
    def _get_default_daily_sal_prv(self):
        for record in self:
            if record.nb_day_base > 0:
                record.daily_sal_prv = record.average_gross_prv / record.nb_day_base
            else:
                record.daily_sal_prv = 0

    def _get_default_not_done_prv(self):
        for record in self:
            if record.stc:
                record.not_done_prv = record.preavis * record.daily_sal_prv
            else:
                record.not_done_prv = 0

    month = fields.Selection(MONTH_LIST,string="Mois de",compute="_get_month_year")
    year = fields.Char("Année",compute="_get_month_year")
    daily_sal_prv = fields.Float("Salaire journalier préavis",store=True, default=_get_default_daily_sal_prv)
    not_done_prv = fields.Float("Préavis non-Effectué", store=True,default=_get_default_not_done_prv)
    calculate_presence = fields.Boolean("Calculer via présence")

    @api.depends('date_from')
    def _get_month_year(self):
        for record in self:
            if record.date_from:
                month_nb = record.date_from.month
                month = MONTH_LIST[month_nb -1]
                record.month = month[0]
                year = record.date_from.year
                record.year = year

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id: # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        self.name = '%s - %s - %s' % (payslip_name, self.employee_id.name or '', format_date(self.env, self.date_from, date_format="MMMM y"))

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _("This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
                (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_to))
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()
        print('___________', self._get_new_worked_days_lines())
        domain = [('employee_id', '=', self.employee_id.id), ('month', '=', self.month), ('year', '=', self.year)]
        SaisieWorkEntry = self.env['saisie.work.entry'].sudo().search(domain)
        # record.worked_days_line_ids = False
        for worked_day in SaisieWorkEntry:
                self.worked_days_line_ids= [(0,0, {
                    'work_entry_type_id': worked_day.work_entry_type.id,
                    'number_of_days': worked_day.number_of_days,
                    'number_of_hours': worked_day.number_of_hours,
                    'saisie_work_entry_id': worked_day.id,
                    'imported': True,
                    })]

    @api.onchange('month', 'employee_id')
    def set_work_days(self):
        for record in self:
            domain = [('employee_id', '=', record.employee_id.id), ('month', '=', record.month), ('year', '=', record.year)]
            SaisieOtherEntry = self.env['saisie.other.entry'].sudo().search(domain)
            record.input_line_ids = False
            for other_entry in SaisieOtherEntry:
                record.input_line_ids = [(0,0, {
                    'input_type_id': other_entry.payslip_input_type.id,
                    'amount': other_entry.amount,
                    'saisie_other_entry': other_entry.id,
                    'imported': True,
                    })]

    @api.onchange('line_ids')
    def line_change(self):
        for record in self:
            record._onchange_employee()
            record.set_work_days()

    @api.onchange('average_gross_prv', 'nb_day_base')
    def _onchange_daily_sal_prv(self):
        for record in self:
            if record.nb_day_base > 0:
                record.daily_sal_prv = record.average_gross_prv / record.nb_day_base
            else:
                record.daily_sal_prv = 0

    @api.onchange('preavis', 'daily_sal_prv')
    def _onchange_set_not_done_prv(self):
        for record in self:
            if record.stc:
                record.not_done_prv = record.preavis * record.daily_sal_prv
            else:
                record.not_done_prv = 0

class HrPayslipRunInherit(models.Model):
    _inherit="hr.payslip.run"

    month = fields.Selection(MONTH_LIST,string="Mois de")
    year = fields.Char("Année")
    calculate_presence = fields.Boolean("Calculer via présence")

class HrLeaveInherit(models.Model):
    _inherit = "hr.leave"

    matricule = fields.Char("Matricule", compute="_get_matricule")

    @api.depends('employee_id')
    def _get_matricule(self):
        for record in self:
            record.matricule = record.employee_id.matricule


class HrLeaveAllocationInherit(models.Model):
    _inherit = "hr.leave.allocation"

    matricule = fields.Char("Matricule", compute="_get_matricule")

    @api.depends('employee_id')
    def _get_matricule(self):
        for record in self:
            record.matricule = record.employee_id.matricule

class HrContractInherit(models.Model):
    _inherit = "hr.contract"

    matricule = fields.Char("Matricule", compute="_get_matricule")

    @api.depends('employee_id')
    def _get_matricule(self):
        for record in self:
            record.matricule = record.employee_id.matricule