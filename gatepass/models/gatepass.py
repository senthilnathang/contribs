# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from datetime import datetime


class GatePass(models.Model):
    _name = 'gatepass.gatepass'
    _description = "Gate Pass"
    _order = "id desc"

    name = fields.Char('Sequence', copy=False)
    partner_id = fields.Many2one('res.partner', 'Party Name')
    date = fields.Date('Date',default=fields.Date.context_today)
    vehicle_number = fields.Char('Vehicle Number',copy=False)
    bill_number = fields.Char('Source Document')
    picking_type = fields.Selection([('incoming', 'Inward'), ('outgoing', 'Outward'), ('internal', 'Internal Transfer')], 'Picking Type')
    user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange', default=lambda self: self.env.user, readonly=True)
    return_type = fields.Selection([('returnable', 'Returnable'), ('non_returnable', 'Non Returnable')], stirng="Return Type",default="non_returnable")
    confirmed_date = fields.Date('Confirmed Date',copy=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('gatepass.gatepass'))
    confirmed_by = fields.Many2one('res.users', 'Confirmed By', readonly=True,copy=False)
    picking_id = fields.Many2one('stock.picking', 'Picking',copy=False)
    return_picking_id = fields.Many2one('stock.picking', 'Return Picking',copy=False)
    return_date = fields.Date('Return Date')
    return_gatepass_id = fields.Many2one('gatepass.gatepass','Return Gate Pass',copy=False)
    remarks = fields.Text('Reason',copy=False)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft', string='State',copy=False)
    gate_pass_count = fields.Integer('Gate Pass Count', default=1)
    gatepass_line_ids = fields.One2many('gatepass.line', 'gatepass_id', 'Gatepass Line',copy=True)

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('gatepass.gatepass')
        return super(GatePass, self).create(values)

    @api.multi
    def copy(self):
        self.ensure_one()
        res = super(GatePass, self)
        return res.copy(default=None)

    @api.onchange('picking_id')
    def onchange_picking_id(self):
        if self.picking_id.origin:
            self.bill_number = self.picking_id.origin

    def get_line_items(self):
        self.gatepass_line_ids.unlink()
        for line in self.picking_id.move_lines:
            if self.picking_id.state == 'done':
                qty = line.quantity_done
            else:
                qty = line.product_uom_qty
            vals = {
                'product_id':line.product_id.id,
                'description':line.product_id.name,
                'product_uom_qty':qty,
                'product_uom':line.product_uom.id,
                'source_location_id':self.picking_id.location_id.id,
                'dest_location_id':self.picking_id.location_dest_id.id,
                'gatepass_id':self.id,
            }
            self.gatepass_line_ids += self.gatepass_line_ids.new(vals)

    @api.multi
    def move_to_confirmed(self):
        self.write({
            'state': 'confirmed',
            'confirmed_by':self.env.user.id,
            'confirmed_date': fields.Date.context_today(self)
        })
        if self.return_type == 'returnable':
            new_id = self.copy()
            if self.picking_type == 'incoming':
                new_id.picking_type = 'outgoing'
            elif self.picking_type == 'outgoing':
                new_id.picking_type = 'incoming'
            new_id.date = self.return_date
            new_id.return_date = False
            new_id.return_type = 'non_returnable'
            new_id.bill_number = 'Return Gate Pass of:'+str(self.name)
            self.return_gatepass_id = new_id

class GatepassLine(models.Model):
    _name = 'gatepass.line'
    _description = 'Gatepass Line'

    product_id = fields.Many2one('product.product', 'Product')
    description = fields.Text('Description')
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=False)
    source_location_id = fields.Many2one('stock.location', 'Source Location')
    dest_location_id = fields.Many2one('stock.location', 'Destination Location')
    gatepass_id = fields.Many2one('gatepass.gatepass', 'Gate Pass')

    @api.onchange('product_id')
    def onchange_product(self):
        self.description = self.product_id.name
        self.product_uom = self.product_id.uom_id.id

class StockPicking(models.Model):
    _inherit = "stock.picking"

    gatepass_id = fields.Many2one('gatepass.gatepass','Gate Pass')

    @api.multi
    def create_gatepass(self):
        if self.gatepass_id:
            self.gatepass_id.sudo().unlink()
        gatepass_id = self.env['gatepass.gatepass'].create({
                'user_id':self.env.user.id,
                'partner_id':self.partner_id.id,
                'date':datetime.now().today(),
                'picking_type':self.picking_type_id.code,
                'picking_id':self.id,
                'bill_number':self.origin
                })
        for line in self.move_lines:
            if self.state == 'done':
                qty = line.quantity_done
            else:
                qty = line.product_uom_qty
            self.env['gatepass.line'].create({
                'product_id':line.product_id.id,
                'description':line.name,
                'product_uom_qty':qty,
                'product_uom':line.product_uom.id,
                'source_location_id':line.location_id.id,
                'dest_location_id':line.location_dest_id.id,
                'gatepass_id':gatepass_id.id
                })
        self.gatepass_id = gatepass_id
        
class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'        
         
    def create_returns(self):
        res = super(ReturnPicking, self).create_returns()
        if self.picking_id:
            self.picking_id.gatepass_id.sudo().unlink()
        return res 
            