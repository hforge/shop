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
from operator import itemgetter

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, Integer, String, Unicode
from itools.gettext import MSG
from itools.stl import stl
from itools.web import ERROR, INFO
from itools.xapian import OrQuery, PhraseQuery

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.datatypes import IntegerRangeDatatype
from shop.products.declination import Declination
from shop.products.enumerate import CategoriesEnumerate, States
from shop.manufacturers import ManufacturersEnumerate
from shop.modules import ShopModule
from shop.suppliers import SuppliersEnumerate
from shop.utils_views import SearchTableFolder_View
from shop.widgets import NumberRangeWidget


class Stock_FillStockOut(SearchTableFolder_View):

    # XXX Problems if we use it to edit prices
    # Problems price pro
    # Problems price with reduction --> has_reduction

    access = 'is_allowed_to_edit'
    title = MSG(u'Fill stock')
    template = '/ui/modules/stock/fill_stock_out.xml'


    search_widgets = [TextWidget('reference', title=MSG(u'Reference')),
                      SelectWidget('abspath', title=MSG(u'Category')),
                      SelectWidget('manufacturer', title=MSG(u'Manufacturer')),
                      SelectWidget('supplier', title=MSG(u'Supplier')),
                      SelectWidget('workflow_state', title=MSG(u'State')),
                      NumberRangeWidget('stock_quantity', title=MSG(u'Quantity in stock'))]

    search_schema = {'reference': String,
                     'abspath': CategoriesEnumerate,
                     'supplier': SuppliersEnumerate,
                     'manufacturer': ManufacturersEnumerate,
                     'workflow_state': States,
                     'stock_quantity': IntegerRangeDatatype}


    def get_query_schema(self):
        return merge_dicts(SearchTableFolder_View.get_query_schema(self),
                           reverse=Boolean(default=False),
                           sort_by=String(default='reference')) # XXX


    def get_schema(self, resource, context):
        references_number = context.get_form_value('references_number',
                              type=Integer) or 0
        schema = {'references_number': Integer}
        for i in range(1, references_number+1):
            schema.update(
              {'reference_%s' % i: String,
               'nb_declinations_%s' % i: Integer,
               'title_%s' % i: Unicode,
               'new_stock_%s' % i: Integer})
            nb_declinations = context.get_form_value('nb_declinations_%s' % i,
                                type=Integer) or 0
            for j in range(1, nb_declinations+1):
                schema['name_%s_%s' % (i, j)] = String
                schema['new_stock_%s_%s' % (i, j)] = Integer
                schema['title_%s_%s' % (i, j)] = Unicode
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
        all_products = context.root.search(format='product')
        # Do
        products = {}
        items = self.get_items(resource, context)
        for i, brain in enumerate(items):
            # It's a product or a declination ?
            if brain.format == 'product':
                brain_product = brain
                brain_declination = None
            else:
                brain_declination = brain
                parent_path = '/'.join(brain_declination.abspath.split('/')[:-1])
                brain_product = all_products.search(abspath=parent_path).get_documents()[0]
            # Get corresponding product
            if products.has_key(brain_product.reference):
                kw = products[brain_product.reference]
            else:
                nb_products = len(products)
                kw = {'id': nb_products + 1,
                      'reference': brain_product.reference,
                      'title': brain_product.title,
                      'href': '/' + '/'.join(brain_product.abspath.split('/')[2:]), # XXX Hack
                      'declinations': [],
                      'nb_declinations': 0,
                      'has_declination': False,
                      'stock_quantity': brain_product.stock_quantity}
                products[brain_product.reference] = kw
            # Get declination
            if brain_declination:
                nb_declinations = kw['nb_declinations']
                d = {'id': nb_declinations + 1,
                     'name': brain_declination.name,
                     'title': brain_declination.declination_title,
                     'stock_quantity': brain_declination.stock_quantity}
                kw['has_declination'] = True
                kw['declinations'].append(d)
                kw['nb_declinations'] = nb_declinations + 1
                products[brain_product.reference] = kw
        # Build namespace
        products = products.values()
        products.sort(key=itemgetter('id'))
        namespace['lines'] = products
        namespace['references_number'] = len(namespace['lines'])
        return namespace


    def get_items(self, resource, context, query=[]):
        query = [OrQuery(
                      PhraseQuery('format', 'product'),
                      PhraseQuery('format', 'product-declination'))]
        return SearchTableFolder_View.get_items(self, resource, context, query)


    def action(self, resource, context, form):
        root = context.root
        references_number = form['references_number']
        for i in range(1, references_number+1):
            reference = form['reference_%s' % i]
            if not reference:
                context.message = ERROR(u'[Error] Line number %s has no reference' % i)
                context.commit = False
                return
            new_stock = form['new_stock_%s' % i]
            search = root.search(reference=reference)
            results = search.get_documents()
            if not results:
                context.message = ERROR(u'[Error] Unknow reference %s' % reference)
                context.commit = False
                return
            # XXX
            #if len(results) > 1:
            #    context.message = ERROR(u'[Error] Reference %s is used %s times.' %
            #                          (reference, len(results)))
            #    context.commit = False
            #    return
            product = root.get_resource(results[0].abspath)
            if new_stock:
                product.set_property('stock-quantity', new_stock)
            nb_declinations = form['nb_declinations_%s' % i]
            if nb_declinations == 0:
                continue
            #declinations = list(product.search_resources(cls=Declination))
            for j in range(1, nb_declinations+1):
                suffix = '_%s_%s' % (i, j)
                name_declination = form['name'+ suffix]
                stock_declination = form['new_stock'+ suffix]
                if stock_declination:
                    declination = product.get_resource(name_declination)
                    declination.set_property('stock-quantity', stock_declination)
        context.message = INFO(u'Stock quantity has been updated')


    def action_generate_pdf(self, resource, context, form):
        context.set_content_type('application/pdf')
        context.set_content_disposition('attachment; filename="Document.pdf"')
        pdf = self.generate_pdf_resupply(resource, context, form)
        return pdf


    def generate_pdf_resupply(self, resource, context, form):
        from datetime import datetime
        from itools.i18n import format_date
        from shop.utils import format_for_pdf
        from itools.pdf import stl_pmltopdf
        accept = context.accept_language
        creation_date = datetime.now()
        creation_date = format_date(creation_date, accept=accept)
        document = resource.get_resource('/ui/modules/stock/pdf_resupply.xml')
        # Build namespace
        namespace =  {'creation_date': creation_date,
                      'lines': []}
        # Supplier
        #supplier = form['supplier']
        #supplier = resource.get_resource(supplier)
        namespace['supplier'] = {
            'title': '',#supplier.get_title(),
            'address': ''}#format_for_pdf(supplier.get_property('address'))}
        # Get references
        references_number = context.get_form_value('references_number',
                              type=Integer) or 0
        for i in range(1, references_number+1):
            kw = {'id': i,
                  'reference': form['reference_%s' % i],
                  'title': form['title_%s' % i],
                  'quantity_to_order': form['new_stock_%s' % i],
                  'declinations': []}
            nb_declinations = form['nb_declinations_%s' % i] or 0
            for j in range(1, nb_declinations + 1):
                suffix = '_%s_%s' % (i, j)
                name_declination = form['name'+ suffix]
                stock_declination = form['new_stock'+ suffix] or 0
                title_declination = form['title'+ suffix]
                kw['declinations'].append({'reference': name_declination,
                                           'title': title_declination,
                                           'quantity_to_order': stock_declination})
            namespace['lines'].append(kw)
        # Generate pdf
        pdf = stl_pmltopdf(document, namespace=namespace)
        #metadata =  {'title': {'en': u'Bill'}}
        #if resource.get_resource('bill.pdf', soft=True):
        #    resource.del_resource('bill.pdf')
        #PDF.make_resource(PDF, resource, 'bill.pdf', body=pdf, **metadata)
        return pdf



class ShopModule_Stock(ShopModule):

    class_id = 'shop_module_stock'
    class_title = MSG(u'Manage stock')
    class_views = ['view']
    class_description = MSG(u'Manage stock')

    view = Stock_FillStockOut()


register_resource_class(ShopModule_Stock)
