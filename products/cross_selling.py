# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Henry Obein <henry@itaapy.com>
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
from random import shuffle

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Integer, Boolean, Unicode
from itools.gettext import MSG
from itools.uri import resolve_uri2, Path
from itools.web import get_context
from itools.xapian import OrQuery, AndQuery, PhraseQuery, NotQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import TextWidget, stl_namespaces
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.future.order import ResourcesOrderedTableFile
from ikaaro.registry import register_resource_class

# Import from shop
from cross_selling_views import AddProduct_View, CrossSelling_Modes
from cross_selling_views import CrossSelling_Configure, CrossSelling_TableView
from shop.utils import get_shop



class ProductSelectorWidget(TextWidget):

    method_to_call = 'add_product'
    template = list(XMLParser(
    """
    <input type="text" id="selector-${name}" size="${size}" name="${name}"
      value="${value}" />
    <input id="selector-button-${name}" type="button" value="..."
      name="selector_button_${name}"
      onclick="popup(';${method}?target_id=selector-${name}&amp;product=${value}',
                     620, 300);"/>
    """, stl_namespaces))


    def get_namespace(self, datatype, value):
        return merge_dicts(TextWidget.get_namespace(self, datatype, value),
                           method=self.method_to_call)



class CrossSellingTable(ResourcesOrderedTable):

    class_id = 'CrossSellingTable'
    class_title = MSG(u'Cross-Selling Table')
    class_handler = ResourcesOrderedTableFile
    class_views = ['configure', 'back']

    form = [ProductSelectorWidget('name', title=MSG(u'Product'))]

    # Views
    configure = CrossSelling_Configure()
    view_table = CrossSelling_TableView()
    add_product = AddProduct_View()
    back = GoToSpecificDocument(specific_document='..',
                                title=MSG(u'See product'))

    # TODO Add get_links, update_links


    @classmethod
    def get_metadata_schema(cls):
        schema = ResourcesOrderedTable.get_metadata_schema()
        schema['mode'] = CrossSelling_Modes
        schema['enabled'] = Boolean
        schema['use_shop_configuration'] = Boolean(default=True)
        schema['products_quantity'] = Integer(default=5)
        schema['filter_text'] = Unicode
        return schema


    def get_products(self, context, product_format, products_folder,
                     categories=None, excluded_products=[]):
        shop = get_shop(self)
        cross_selling_resource = self
        if self.get_property('use_shop_configuration'):
            cross_selling_resource = shop.get_resource('cross-selling')
        if cross_selling_resource.get_property('enabled') is False:
            return

        root = context.root
        mode = cross_selling_resource.get_property('mode')
        products_quantity = cross_selling_resource.get_property(
                                                      'products_quantity')

        # Base query
        query = AndQuery(PhraseQuery('format', product_format),
                         PhraseQuery('workflow_state', 'public'),
                         PhraseQuery('has_categories', True))
        # Excluded products query
        if excluded_products:
            exclude_query = OrQuery(*[ PhraseQuery('abspath', str(abspath))
                                       for abspath in excluded_products ])
            query = AndQuery(query, NotQuery(exclude_query))
        # Filter on product title
        filter_text = cross_selling_resource.get_property('filter_text')
        if filter_text:
            query = AndQuery(query, PhraseQuery('title', filter_text))
        # Categories query
        if categories and mode.endswith('_category'):
            query_categorie = OrQuery(*[ PhraseQuery('categories', x)
                                         for x in categories ])
            query = AndQuery(query, query_categorie)

        if mode.startswith('random'):
            # Random selection
            results = root.search(query)
            brains = list(results.get_documents())
            shuffle(brains)
            for brain in brains[:products_quantity]:
                yield root.get_resource(brain.abspath)
        elif mode.startswith('last'):
            # Last products
            results = root.search(query)
            brains = list(results.get_documents(sort_by='ctime',
                            reverse=True, size=products_quantity))
            for brain in brains:
                yield root.get_resource(brain.abspath)
        elif mode == 'table':
            # Selection in cross selling table
            handler = cross_selling_resource.handler
            get_value = handler.get_record_value
            ids = list(handler.get_record_ids_in_order())
            names = []
            for id in ids[:products_quantity]:
                record = handler.get_record(id)
                path = get_value(record, 'name')
                names.append(path)
                yield products_folder.get_resource(path)

            if len(ids) < products_quantity:
                not_query = NotQuery(OrQuery(*[ PhraseQuery('name', name)
                                                for name in names ]))
                # Complete with random selection
                diff = products_quantity - len(ids)
                results = root.search(AndQuery(query, not_query))
                brains = list(results.get_documents())
                shuffle(brains)
                for brain in brains[:diff]:
                    yield root.get_resource(brain.abspath)


    def get_links(self):
        shop = get_shop(self)
        base = shop.get_canonical_path()
        links = []

        handler = self.handler
        get_value = handler.get_record_value
        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            links.append(str(resolve_uri2(base, 'products/%s' % name)))

        return links


    def update_links(self, source, target):
        shop = get_shop(self)
        base = shop.get_canonical_path()
        target_name = Path(target).get_name()
        links = []

        handler = self.handler
        get_value = handler.get_record_value
        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            path = str(resolve_uri2(base, 'products/%s' % name))
            if path == source:
                handler.update_record(record.id, **{'name': target_name})
        get_context().database.change_resource(self)



register_resource_class(CrossSellingTable)
