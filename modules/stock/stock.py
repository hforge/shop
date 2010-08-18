# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from copy import deepcopy
from datetime import datetime

# Import from itools
from itools.csv import Table as BaseTable
from itools.datatypes import Enumerate, Integer, String
from itools.gettext import MSG
from itools.pdf import stl_pmltopdf
from itools.i18n import format_date
from itools.stl import stl
from itools.web import STLView, get_context
from itools.web import ERROR, INFO, STLForm
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.file import PDF
from ikaaro.forms import SelectWidget, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.enumerate_table import EnumerateTable_to_Enumerate
from shop.products.declination import Declination
from shop.products.enumerate import CategoriesEnumerate, ProductModelsEnumerate
from shop.suppliers import SuppliersEnumerate
from shop.utils_views import SearchTableFolder_View, get_search_query
from shop.listeners import register_listener
from shop.modules import ShopModule
from shop.utils import get_skin_template, format_for_pdf


class Stock_Operations_BaseTable(BaseTable):

    record_properties = {
      'reference': String,
      'quantity': Integer,
      }



class Stock_OperationsResupply(Table):

    class_id = 'shop_module_stock_operations'
    class_title = MSG(u'Products')
    class_handler = Stock_Operations_BaseTable

    class_views = ['view']

    form = [
        TextWidget('reference', title=MSG(u'Reference')),
        TextWidget('quantity', title=MSG(u'Quantity'))]

#
#
#class Stock_Resupply(STLForm):
#
#    access = 'is_allowed_to_edit'
#    title = MSG(u'Resupply stock')
#    template = '/ui/backoffice/stock/resupply.xml'
#
#    search_schema = {'supplier': SuppliersEnumerate}
#
#    search_widgets = [
#        SelectWidget('supplier', title=MSG(u'Supplier'),
#                      has_empty_option=False),
#        ]
#
#    def get_query_schema(self):
#        return self.search_schema
#
#
#    def get_schema(self, resource, context):
#        references_number = context.get_form_value('references_number',
#                              type=Integer) or 0
#        schema = {'supplier': SuppliersEnumerate}
#        for i in range(1, references_number+1):
#            schema.update(
#              {'reference_%s' % i: String,
#               'quantity_to_order_%s' % i: Integer(mandatory=True)})
#        return schema
#
#
#    def get_search_namespace(self, resource, context):
#        query = context.query
#        namespace = {'widgets': []}
#        for widget in self.search_widgets:
#            value = context.query[widget.name]
#            html = widget.to_html(self.search_schema[widget.name], value)
#            namespace['widgets'].append({'title': widget.title,
#                                         'html': html})
#        return namespace
#
#
#    def get_namespace(self, resource, context):
#        root = context.root
#        namespace = self.get_search_namespace(resource, context)
#        namespace['lines'] = []
#        supplier = context.query['supplier']
#        if supplier is None:
#            return namespace
#        namespace['supplier'] = supplier
#        format = resource.parent.product_class.class_id
#        query = [PhraseQuery('format', format),
#                 PhraseQuery('supplier', supplier)]
#        search = root.search(AndQuery(*query))
#        for i, brain in enumerate(search.get_documents()):
#            product = root.get_resource(brain.abspath)
#            kw = {'id': i+1,
#                  'reference': product.get_property('reference'),
#                  'title': product.get_title(),
#                  'href': context.get_link(product),
#                  'stock_quantity': product.get_property('stock-quantity'),
#                  'quantity_to_order': product.get_property('stock-quantity') +5}
#            namespace['lines'].append(kw)
#        return namespace
#
#
#    def action(self, resource, context, form):
#        context.set_content_type('application/pdf')
#        context.set_content_disposition('attachment; filename="Document.pdf"')
#        pdf = self.generate_pdf_resupply(resource, context, form)
#        return pdf
#
#
#    def generate_pdf_resupply(self, resource, context, form):
#        accept = context.accept_language
#        creation_date = datetime.now()
#        creation_date = format_date(creation_date, accept=accept)
#        document = resource.get_resource('/ui/backoffice/stock/pdf_resupply.xml')
#        # Build namespace
#        namespace =  {'creation_date': creation_date,
#                      'lines': []}
#        # Supplier
#        supplier = form['supplier']
#        supplier = resource.get_resource(supplier)
#        namespace['supplier'] = {
#            'title': supplier.get_title(),
#            'address': format_for_pdf(supplier.get_property('address'))}
#        # Get references
#        references_number = context.get_form_value('references_number',
#                              type=Integer) or 0
#        for i in range(1, references_number+1):
#            kw = {'id': i,
#                  'reference': form['reference_%s' % i],
#                  'quantity_to_order': form['quantity_to_order_%s' % i]}
#            namespace['lines'].append(kw)
#        # Generate pdf
#        pdf = stl_pmltopdf(document, namespace=namespace)
#        metadata =  {'title': {'en': u'Bill'}}
#        if resource.get_resource('bill.pdf', soft=True):
#            resource.del_resource('bill.pdf')
#        PDF.make_resource(PDF, resource, 'bill.pdf', body=pdf, **metadata)
#        return pdf



class Stock_FillStockOut(SearchTableFolder_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'Fill stock')
    template = '/ui/modules/stock/fill_stock_out.xml'


    search_widgets = [TextWidget('reference', title=MSG(u'Reference')),
                      SelectWidget('abspath', title=MSG(u'Category')),
                      SelectWidget('product_model', title=MSG(u'Product model'))]

    search_schema = {'reference': String,
                     'abspath': CategoriesEnumerate,
                     'product_model': ProductModelsEnumerate}

    def get_schema(self, resource, context):
        references_number = context.get_form_value('references_number',
                              type=Integer) or 0
        schema = {'references_number': Integer}
        for i in range(1, references_number+1):
            schema.update(
              {'reference_%s' % i: String,
               'nb_declinations_%s' % i: Integer,
               'new_stock_%s' % i: Integer})
            nb_declinations = context.get_form_value('nb_declinations_%s' % i,
                                type=Integer) or 0
            for j in range(1, nb_declinations+1):
                schema['name_%s_%s' % (i, j)] = String
                schema['new_stock_%s_%s' % (i, j)] = Integer
        return schema


    def get_namespace(self, resource, context):
        namespace = {'lines': []}
        # Search
        search_template = resource.get_resource(self.search_template)
        search_namespace = self.get_search_namespace(resource, context)
        namespace['search'] = stl(search_template, search_namespace)
        # Is a research ?
        if context.uri.query.has_key('search') is False:
            return namespace
        # Get all declinations (for optimization purpose)
        all_declinations =  context.root.search(format=Declination.class_id)
        # Do
        root = context.root
        items = self.get_items(resource, context)
        for i, brain in enumerate(items):
            declinations = all_declinations.search(parent_path=brain.abspath).get_documents()
            nb_declinations = len(declinations)
            kw = {'id': i+1,
                  'reference': brain.reference,
                  'title': brain.title,
                  'href': '',
                  'declinations': [],
                  'has_declination': nb_declinations > 0,
                  'nb_declinations': nb_declinations,
                  'stock_quantity': brain.stock_quantity}
            for j, declination in enumerate(declinations):
                d = {'id': j+1,
                     'name': declination.name,
                     'title': declination.declination_title,
                     'stock_quantity': declination.stock_quantity}
                kw['declinations'].append(d)
            namespace['lines'].append(kw)
            namespace['references_number'] = len(namespace['lines'])
        return namespace


    def get_items(self, resource, context, query=[]):
        query = [PhraseQuery('format', 'product')]
        return SearchTableFolder_View.get_items(self, resource, context, query)


    def action(self, resource, context, form):
        root = context.root
        references_number = form['references_number']
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
            if len(results) > 1:
                context.message = ERROR(u'Reference %s is used %s times.' %
                                      (reference, len(results)))
                #return
            product = root.get_resource(results[0].abspath)
            if new_stock:
                product.set_property('stock-quantity', new_stock)
            nb_declinations = form['nb_declinations_%s' % i]
            if nb_declinations == 0:
                continue
            declinations = list(product.search_resources(cls=Declination))
            for j in range(1, nb_declinations+1):
                suffix = '_%s_%s' % (i, j)
                name_declination = form['name'+ suffix]
                stock_declination = form['new_stock'+ suffix]
                if stock_declination:
                    declination = product.get_resource(name_declination)
                    declination.set_property('stock-quantity', stock_declination)
        context.message = INFO(u'Stock quantity has been updated')



class ShopModule_Stock(ShopModule):

    class_id = 'shop_module_stock'
    class_title = MSG(u'Manage stock')
    class_views = ['view']
    class_description = MSG(u'Manage stock')

    view = Stock_FillStockOut()


    def register_listeners(self):
        register_listener('product', 'stock-quantity', self)
        register_listener('product-declination', 'stock-quantity', self)


    def alert(self, action, resource, class_id, property_name, old_value, new_value):
        print 'resource', resource
        print 'action', action
        print 'class_id', class_id
        print 'Property_name', property_name
        print 'old_value', old_value
        print 'new_value', new_value
        operations = self.get_resource('operations')
        operations.handler.add_record({'reference': resource.get_property('reference'),
                                       'quantity': old_value - new_value})


register_resource_class(ShopModule_Stock)
