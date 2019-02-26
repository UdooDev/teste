# -*- coding: utf-8 -*-

import io
from odoo import models, fields, api
import base64
import datetime
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import csv

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def create_xls_consignment_report(self):
        estoque = self.env['stock.quant'].search([('location_id.id', '=', self.consignee_location_id.id)])

        if len(estoque) > 0:            
            cabecalho = "Mapa de Consignação Editora Hedra\ncomercial@hedra.com.br\n11-3097-8304\n\n"
            empresa = self.name + "\n"
            data = datetime.datetime.now().strftime('%d-%m-%Y')
            campos = "\n\nISBN,Titulo,Quantidade,Valor de Custo,Valor de Venda,Valor Total,Acerto,Reposição\n"

            arquivo = cabecalho + empresa + data + campos

            for produto in estoque:
                isbn = produto.product_id.ean13
                titulo = produto.product_id.name
                quantidade = produto.quantity
                val_custo = produto.product_id.standard_price
                val_venda = produto.product_id.list_price
                total = val_custo * quantidade

                linha = "%s,%s,%d,%.2f,%.2f,%.2f\n" % (isbn, titulo, int(quantidade), val_custo, val_venda, total)
                arquivo = arquivo + linha

            out_move = self.env['stock.move'].search([('location_id', '=', self.consignee_location_id.id)])
            if out_move:
                t_sold = "\n\n\n Total Sold Products \n\n"
                arquivo = arquivo + t_sold
                for produto in out_move:
                    isbn = produto.product_id.ean13
                    titulo = produto.product_id.name
                    quantidade = produto.product_uom_qty
                    val_custo = produto.product_id.standard_price
                    val_venda = produto.product_id.list_price
                    total = val_custo * quantidade
                    linha = "%s,%s,%d,%.2f,%.2f,%.2f\n" % (isbn, titulo, int(quantidade), val_custo, val_venda, total)
                    arquivo = arquivo + linha

            mode = 'manual'
            if self._context.get('mode') and self._context.get('mode') == 'auto':
                mode = 'auto'
            
            attach = self.env['ir.attachment'].create({
                    'name': u'RelatorioConsignacao.xlsx',
                    'datas': base64.b64encode(arquivo.encode()),
                    'datas_fname': "RelatorioConsignacao.xlsx",
                    'res_model': 'mail.compose.message',
                    'res_id': 0,
                    'consignment_partner_id': self.id,
                    'consignment_mode': mode
                })

            print ("attachment_id-----------",attach)
            return attach.id
        else:
            return False

    @api.multi
    def action_view_poconsignment_products(self):
        self.ensure_one()
        estoque = self.env['stock.quant'].search([('location_id.id', '=', self.consignee_location_id.id)])
        if len(estoque) > 0:
            imd = self.env['ir.model.data']
            list_view_id = imd.xmlid_to_res_id('stock.view_stock_quant_tree')            
            form_view_id = imd.xmlid_to_res_id('stock.view_stock_quant_form')
            action = self.env.ref('client-consignment.consignee_open_quants').read()[0]
            action['domain'] = "[('consig_op_type', '=', 'purchase'), ('location_id','=',%s)]" % self.consignee_location_id.id
            action['context'] = {'search_default_internal_loc': 1, 'search_default_productgroup': 1}
            action['views'] = [[list_view_id, 'tree'], [form_view_id, 'form']]
            return action
        else:
            raise Warning('Este cliente não possui produtos em consignado.')

    # @api.multi
    # def action_view_soconsignment_products(self):
    #     self.ensure_one()
        
    #     estoque = self.env['stock.quant'].search([('location_id.id', '=', self.consignee_location_id.id)])
        
    #     if len(estoque) > 0:
    #         imd = self.env['ir.model.data']
    #         list_view_id = imd.xmlid_to_res_id('stock.view_move_tree')
    #         form_view_id = imd.xmlid_to_res_id('stock.view_move_form')
    #         action = self.env.ref('client-consignment-purchase.consignee_open_stock_move').read()[0]
    #         action['domain'] = "[('state', '=', 'done'),('location_id','=',%s)]" % self.consignee_location_id.id
    #         action['context'] = {'search_default_groupby_location_id': 1, 'search_default_by_product': 1}
    #         action['views'] = [[list_view_id, 'tree'], [form_view_id, 'form']]
    #         return action
    #     else:
    #         raise Warning('Este cliente não possui produtos em consignado.')
    
    # @api.model
    # def consignment_report_cron(self):
    #     print ("##### consignment_report_cron [START] #####")
        
    #     customers = self.search([('send_auto_email','=',True)])
        
    #     template_id = self.env['ir.model.data'].get_object_reference('client-consignment',
    #                                                                  'email_template_partner_consignment_report')[1]
    #     for each_cst in customers:
    #         attachment_id = each_cst.with_context({'mode':'auto'}).create_xls_consignment_report()
        
    #         self.env['mail.template'].browse(template_id).send_mail(each_cst.id)
        
    #     print ("##### consignment_report_cron [END] #####")

    # @api.one
    # def _compute_sale_order_count(self):
    #     super(res_partner, self)._compute_sale_order_count()

    #     sale_data = self.env['sale.order'].read_group(domain=[('partner_id', 'child_of', self.ids)],
    #                                                  fields=['partner_id'], groupby=['partner_id'])
    #     cons_count = self.env['sale.order'].search_count([('partner_id','=', self.id),('order_type','=','con_order')])

    #     partner_child_ids = self.read(['child_ids'])
    #     mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in sale_data])
    #     for partner in self:

    #        # let's obtain the partner id and all its child ids from the read up there
    #         item = next(p for p in partner_child_ids if p['id'] == partner.id)
    #         partner_ids = [partner.id] + item.get('child_ids')
    #         # then we can sum for all the partner's child
    #         partner.sale_order_count = sum(mapped_data.get(child, 0) for child in partner_ids)
    #     self.sale_order_count -= cons_count

class mail_compose_message(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def cancel_send_email(self):
        self.env['ir.attachment'].search([('id', '=', self.attachment_ids.id)]).unlink()

    @api.model
    def default_get(self, fields):
        result = super(mail_compose_message, self).default_get(fields)

        consignment_template = self.env.ref("client-consignment-purchase.email_template_po_partner_consignment_report")

        if result.get('template_id') and result.get('template_id') == consignment_template.id:
            if self._context and self._context.get('active_id'):
                attachment_id = self.env['res.partner'].browse(self._context.get('active_id')).create_xls_consignment_report()

                if attachment_id:
                    result['attachment_ids'] = [attachment_id]

        return result

class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    consignment_partner_id = fields.Many2one('res.partner','Relatório para:', readonly=True)
    
    consignment_mode = fields.Selection([('auto','Automatic'),('manual','Manual')], string="Modo de Criação")
    
    @api.model
    def create(self, vals):
        attach = super(ir_attachment, self).create(vals)

        return attach
