
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

class consignment_purchase_order_line(models.Model):
    _name = 'consignment.purchase.order.line'

    order_id = fields.Many2one("consignment.order", string="Order", )
    product_id = fields.Many2one("product.product", string="Product",required=True)
    name = fields.Text('Description', required=True,)
    quantity = fields.Integer("Quantity")
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True, invisible=True)
    price_unit = fields.Float('Unit Price', store=True, digits= dp.get_precision('Product Price'), 
                                compute='_compute_subtotal', readonly=True)
    price_subtotal = fields.Float(string='Subtotal', store=True, readonly=True, compute='_compute_subtotal',
                                    digits= dp.get_precision('Account'),)
    consignment_stock = fields.Float(string='Consignment Stock',
                                        compute='_compute_consignment_stock')

    @api.one
    @api.depends('product_id')
    def _compute_consignment_stock(self):
        if not self.product_id:
            return
        consignent_location = self.order_id.partner_id.consignee_location_id
        if not consignent_location:
            return False
        # Fetch the stock at this customer's consignee location
        consignment_quants = self.env['stock.quant'].search([('location_id','=',consignent_location.id),
                                                              ('product_id','=', self.product_id.id)
                                                            ])
        line_data = []
        product_qty = 0
        for each_quant in consignment_quants:
            product_qty += each_quant.qty

        self.consignment_stock = product_qty



    @api.one
    @api.depends('quantity', 'product_id','order_id.pricelist_id')
    def _compute_subtotal(self):
        price_unit = 0
        subtotal = 0
        if self.product_id and self.quantity:
            price_unit = self.order_id.pricelist_id.price_get(self.product_id.id, self.quantity, self.order_id.partner_id.id)[self.order_id.pricelist_id.id]
        self.price_unit = price_unit or 0.0
        self.price_subtotal = self.quantity*self.price_unit


        


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.category_id.id != self.product_uom.category_id.id):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.quantity,
            date=self.order_id.order_date,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name
        vals['quantity'] = 1
        vals['price_unit'] = self.order_id.pricelist_id.price_get(self.product_id.id, vals['quantity'], self.order_id.partner_id.id)[self.order_id.pricelist_id.id]
        print ("vals---------",vals)
        self.update(vals)

        return {'domain': domain}

class consignment_purchase(models.Model):
    _name = 'consignment.purchase'

    partner_id = fields.Many2one("res.partner", string="Customer", domain=[('customer','=',True)])
    order_date = fields.Datetime("Date", default=fields.Datetime.now)
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),
                              ('transferred','Transferred'),('cancelled','Cancelled')], string='State', default='draft')
    name = fields.Char("Name",default=lambda self: self.env['ir.sequence'].next_by_code('con.purchase'))
    client_order_ref = fields.Char("Client Ref.",readonly=True)
    order_line = fields.One2many('consignment.purchase.order.line','order_id','Order Lines')

    @api.multi
    def button_confirm(self):
        self.state = 'confirmed'

    @api.multi
    def button_transfer(self):
        self.state = 'transferred'

    @api.multi
    def button_cancel(self):
        self.state = 'cancelled'

    @api.multi
    def button_restock(self):
        return True
        
    @api.multi
    def button_invoice_view(self):
        
        return True



class consignment_purchase_line(models.Model):
    _name = 'consignment.purchase.line'

    order_id = fields.Many2one("consignment.purchase", string="Order")
    product_id = fields.Many2one("product.template", string="Product")
    description = fields.Char(string="Description")
    quantity = fields.Integer("Quantity")
    unit_price = fields.Float("Unit Price")
    price_subtotal = fields.Float("Subtotal")
 