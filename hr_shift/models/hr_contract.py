# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import Warning
from odoo import models, fields, api, _
from datetime import datetime
from datetime import time as datetime_time
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class HREmployeeShift(models.Model):
    _name = 'hr.employee.shift'
    _description = 'Employee Shift'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    def _get_current_company(self):
        return self.env['res.company']._company_default_get()

    company_id = fields.Many2one(string="Current Company", comodel_name='res.company', default=_get_current_company)
    name = fields.Char('Name', required=True, compute='compute_no_of_days', readonly=True, states={'draft': [('readonly', False)]})
    start_date = fields.Datetime(string="Date From", required=True, readonly=True, states={'draft': [('readonly', False)]})
    end_date = fields.Datetime(string="Date To", required=True, readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, required=True, states={'draft': [('readonly', False)]})
    hr_shift = fields.Many2one('resource.calendar', string="Shift", readonly=True, required=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned')], 'Type', default='draft', required=True)
    shift_run_id = fields.Many2one('employee.shift.run', 'Batch', states={'draft': [('readonly', False)]})
    no_of_days = fields.Float('No.of Days', compute='compute_no_of_days', store=True)

    @api.multi
    def draft_shift_run(self):
        self.write({'state':'draft'})

    @api.multi
    def close_shift(self):
        for shift in self:
            over_lap1 = self.search_count([('employee_id', '=', shift.employee_id.id), ('start_date', '>=', shift.start_date), ('start_date', '<=', shift.end_date),('id', '!=', self.id)])
            over_lap2 = self.search_count([('employee_id', '=', shift.employee_id.id), ('end_date', '>=', shift.start_date), ('end_date', '<=', shift.end_date),('id', '!=', self.id)])
            if over_lap1:
                raise ValidationError(_('You can not have 2 shifts that overlaps on same day!'))
            if over_lap2:
                raise ValidationError(_('You can not have 2 shifts that overlaps on same day!'))
            self.write({'state':'assigned'})

    @api.multi
    def schedule_shift(self):
        for employee in self.env['hr.employee'].search([('active','=',True)]):
            over_lap1 = self.env['employee.shift'].search([('employee_id', '=', employee.id), ('start_date', '<=', fields.Datetime.now()), ('end_date', '>=', fields.Datetime.now())])
            _logger.info(over_lap1)
            if over_lap1:
                employee.write({'resource_calendar_id':over_lap1.hr_shift.id})

    @api.depends('start_date','end_date','hr_shift')
    def compute_no_of_days(self):
        for line in self:
            if line.start_date and line.end_date:
                d1 = datetime.strptime(str(line.start_date), "%Y-%m-%d %H:%M:%S")
                d2 = datetime.strptime(str(line.end_date), "%Y-%m-%d %H:%M:%S")
                line.no_of_days = (d2 - d1).days + 1
                if line.hr_shift and line.no_of_days:
                    line.name = line.hr_shift.name + ' for ' + str(line.no_of_days) + 'days'


class EmployeeShiftRun(models.Model):
    _name = 'employee.shift.run'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_current_company(self):
        return self.env['res.company']._company_default_get()

    company_id = fields.Many2one(string="Current Company", comodel_name='res.company', default=_get_current_company)
    name = fields.Char('Name', required=True, readonly=True, states={'draft': [('readonly', False)]})
    start_date = fields.Datetime(string="Date From", required=True, readonly=True,  states={'draft': [('readonly', False)]})
    end_date = fields.Datetime(string="Date To", required=True, readonly=True, states={'draft': [('readonly', False)]})
    employee_shift_ids = fields.One2many('employee.shift', 'shift_run_id', string='Employee', readonly=True, states={'draft': [('readonly', False)]})
    hr_shift = fields.Many2one('resource.calendar', string="Shift", required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned')], 'shift', default='draft', required=True)

    @api.multi
    def close_shift_run(self):
        for shift in self.employee_shift_ids:
            shift.close_shift()
        self.write({'state':'assigned'})

    @api.multi
    def draft_shift_run(self):
        self.employee_shift_ids.write({'state':'draft'})
        self.write({'state':'draft'})

class HrshiftEmployees(models.TransientModel):
    _name = 'hr.shift.employees'
    _description = 'Generate Shifts for all selected employees'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_shift_rel', 'shift_id', 'employee_id', 'Employees')

    @api.multi
    def compute_sheet(self):
        shift = self.env['hr.employee.shift']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['employee.shift.run'].browse(active_id).read(['start_date','end_date','hr_shift','state'])
        to_date = run_data.get('end_date')
        start_date = run_data.get('start_date')
        hr_shift = run_data.get('hr_shift')
        state = run_data.get('state')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate appraisal(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            _logger.info(hr_shift)
            res = {
                'employee_id': employee.id,
                'end_date' : to_date,
                'start_date': start_date,
                'hr_shift': hr_shift[0],
                'state': state,
                'shift_run_id' : active_id
            }
            shift += self.env['hr.employee.shift'].create(res)
        return {'type': 'ir.actions.act_window_close'}
