# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Sylvain Taverne <sylvain@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from itools
from itools.datatypes import Integer, String
from itools.gettext import MSG
from itools.i18n import format_date
from itools.pdf import stl_pmltopdf
from itools.web import ERROR, INFO, STLForm

# Import from ikaaro
#from ikaaro.file import PDF

# Import from shop
from shop.suppliers import SuppliersEnumerate


class Stock_Resupply(STLForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Resupply stock')
    template = '/ui/shop/stock/resupply.xml'

    def get_namespace(self, resource, context):
        root = context.root
        namespace = {'lines': []}
        format = resource.parent.product_class.class_id
        search = root.search(format=format)
        for i, brain in enumerate(search.get_documents()):
            product = root.get_resource(brain.abspath)
            # XXX By default we take first supplier
            suppliers = product.get_property('supplier')
            supplier = suppliers[0] if suppliers else '-'
            kw = {'id': i+1,
                  'reference': product.get_property('reference'),
                  'title': product.get_title(),
                  'href': context.get_link(product),
                  'supplier': SuppliersEnumerate.get_value(supplier),
                  'stock_quantity': product.get_property('stock-quantity'),
                  'new_stock': product.get_property('stock-quantity') +5}
            namespace['lines'].append(kw)
        return namespace


    def action(self, resource, context):
        self.generate_pdf_resupply(context)


    def generate_pdf_resupply(self, context):
        accept = context.accept_language
        creation_date = self.get_property('creation_datetime')
        creation_date = format_date(creation_date, accept=accept)
        # Delete old bill
        if self.get_resource('bill', soft=True):
            self.del_resource('bill')
        document = self.get_resource('/ui/shop/stock/pdf_resupply.xml')
        namespace =  {'creation_date': creation_date}
        pdf = stl_pmltopdf(document, namespace=namespace)
        #metadata =  {'title': {'en': u'Bill'}}
        #PDF.make_resource(PDF, self, 'bill', body=pdf, **metadata)
        return pdf


class Stock_FillStockOut(STLForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Fill stock')
    template = '/ui/shop/stock/fill_stock_out.xml'

    def get_schema(self, resource, context):
        references_number = context.get_form_value('references_number',
                              type=Integer) or 0
        schema = {}
        for i in range(1, references_number+1):
            schema.update(
              {'reference_%s' % i: String,
               'new_stock_%s' % i: Integer(mandatory=True)})
        return schema


    def action(self, resource, context, form):
        root = context.root
        references_number = context.get_form_value('references_number',
                              type=Integer) or 0
        for i in range(1, references_number+1):
            reference = form['reference_%s' % i]
            if not reference:
                continue
            new_stock = form['new_stock_%s' % i]
            search = root.search(reference=reference)
            results = search.get_documents()
            if not results:
                context.message = ERROR(u'Unknow reference %s' % reference)
                return
            product = root.get_resource(results[0].abspath)
            product.set_property('stock-quantity', new_stock)
        context.message = INFO(u'Stock quantity has been updated')
