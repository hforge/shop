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

# Import from standard library
from datetime import datetime

# Import from itools
from itools.datatypes import Integer, String
from itools.gettext import MSG
from itools.i18n import format_date
from itools.pdf import stl_pmltopdf
from itools.web import ERROR, INFO, STLForm
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.file import PDF
from ikaaro.forms import SelectWidget

# Import from shop
from shop.suppliers import SuppliersEnumerate
from shop.utils import format_for_pdf


class Stock_Resupply(STLForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Resupply stock')
    template = '/ui/shop/stock/resupply.xml'

    search_schema = {'supplier': SuppliersEnumerate}

    search_widgets = [
        SelectWidget('supplier', title=MSG(u'Supplier'),
                      has_empty_option=False),
        ]

    def get_query_schema(self):
        return self.search_schema


    def get_schema(self, resource, context):
        references_number = context.get_form_value('references_number',
                              type=Integer) or 0
        schema = {'supplier': SuppliersEnumerate}
        for i in range(1, references_number+1):
            schema.update(
              {'reference_%s' % i: String,
               'quantity_to_order_%s' % i: Integer(mandatory=True)})
        return schema


    def get_search_namespace(self, resource, context):
        query = context.query
        namespace = {'widgets': []}
        for widget in self.search_widgets:
            value = context.query[widget.name]
            html = widget.to_html(self.search_schema[widget.name], value)
            namespace['widgets'].append({'title': widget.title,
                                         'html': html})
        return namespace


    def get_namespace(self, resource, context):
        root = context.root
        namespace = self.get_search_namespace(resource, context)
        namespace['lines'] = []
        supplier = context.query['supplier']
        if supplier is None:
            return namespace
        namespace['supplier'] = supplier
        format = resource.parent.product_class.class_id
        query = [PhraseQuery('format', format),
                 PhraseQuery('supplier', supplier)]
        search = root.search(AndQuery(*query))
        for i, brain in enumerate(search.get_documents()):
            product = root.get_resource(brain.abspath)
            kw = {'id': i+1,
                  'reference': product.get_property('reference'),
                  'title': product.get_title(),
                  'href': context.get_link(product),
                  'stock_quantity': product.get_property('stock-quantity'),
                  'quantity_to_order': product.get_property('stock-quantity') +5}
            namespace['lines'].append(kw)
        return namespace


    def action(self, resource, context, form):
        response = context.response
        response.set_header('Content-Type', 'application/pdf')
        response.set_header('Content-Disposition',
                            'attachment; filename="Document.pdf"')
        pdf = self.generate_pdf_resupply(resource, context, form)
        return pdf


    def generate_pdf_resupply(self, resource, context, form):
        accept = context.accept_language
        creation_date = datetime.now()
        creation_date = format_date(creation_date, accept=accept)
        document = resource.get_resource('/ui/shop/stock/pdf_resupply.xml')
        # Build namespace
        namespace =  {'creation_date': creation_date,
                      'lines': []}
        # Supplier
        supplier = form['supplier']
        supplier = resource.get_resource(supplier)
        namespace['supplier'] = {
            'title': supplier.get_title(),
            'address': format_for_pdf(supplier.get_property('address'))}
        # Get references
        references_number = context.get_form_value('references_number',
                              type=Integer) or 0
        for i in range(1, references_number+1):
            kw = {'id': i,
                  'reference': form['reference_%s' % i],
                  'quantity_to_order': form['quantity_to_order_%s' % i]}
            namespace['lines'].append(kw)
        # Generate pdf
        pdf = stl_pmltopdf(document, namespace=namespace)
        metadata =  {'title': {'en': u'Bill'}}
        if resource.get_resource('bill.pdf', soft=True):
            resource.del_resource('bill.pdf')
        PDF.make_resource(PDF, resource, 'bill.pdf', body=pdf, **metadata)
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


    def get_namespace(self, resource, context):
        root = context.root
        namespace = {'lines': []}
        #format = resource.parent.product_class.class_id
        #search = root.search(format=format)
        #for i, brain in enumerate(search.get_documents()):
        #    if i > 20:
        #        break
        #    product = root.get_resource(brain.abspath)
        #    # XXX By default we take first supplier
        #    suppliers = product.get_property('supplier')
        #    supplier = suppliers[0] if suppliers else '-'
        #    kw = {'id': i+1,
        #          'reference': product.get_property('reference'),
        #          'title': product.get_title(),
        #          'href': context.get_link(product),
        #          'stock_quantity': product.get_property('stock-quantity')}
        #    namespace['lines'].append(kw)
        return namespace


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
