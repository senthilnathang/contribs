# -*- coding: utf-8 -*-
# Senthilnathan G.

from openerp import _, api, fields, models

class latest_log(models.Model):
    _name = "latest.log"
    _description = "Latest Log"

    name = fields.Char(string='Menu Name')
    short_name = fields.Char(string='Short Name')    
    action = fields.Char(string='Action')    
    user_id = fields.Many2one('res.users', string='Viewed By')
    last_log = fields.Datetime(string='Last Log')


