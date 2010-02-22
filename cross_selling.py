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
from itools.gettext import MSG
from itools.uri import Path, resolve_uri2, get_reference
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
from cross_selling_views import AddProduct_View
from cross_selling_views import CrossSelling_Configure, CrossSelling_TableView
from cross_selling_views import cross_selling_schema
from utils import get_shop



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
    class_version = '20090223'
    class_views = ['configure', 'back']

    form = [ProductSelectorWidget('name', title=MSG(u'Product'))]

    # Views
    configure = CrossSelling_Configure()
    view_table = CrossSelling_TableView()
    add_product = AddProduct_View()
    back = GoToSpecificDocument(specific_document='..',
                                title=MSG(u'See product'))

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ResourcesOrderedTable.get_metadata_schema(),
                           cross_selling_schema)


    def get_products(self, context, product_format, products_folder,
                     categories=None, excluded_products=[]):
        shop = get_shop(self)
        table = self
        if self.get_property('use_shop_configuration'):
            table = shop.get_resource('cross-selling')
        if table.get_property('enabled') is False:
            return

        root = context.root
        products_quantity = table.get_property('products_quantity')

        # Base query
        query = [PhraseQuery('format', product_format),
                 PhraseQuery('workflow_state', 'public'),
                 PhraseQuery('is_buyable', True)]
        # Excluded products query
        if excluded_products:
            exclude_query = OrQuery(*[ PhraseQuery('abspath', str(abspath))
                                       for abspath in excluded_products ])
            query.append(NotQuery(exclude_query))
        # Filter on product title
        filter_text = table.get_property('filter_text')
        if filter_text:
            query.append(PhraseQuery('title', filter_text))
        # Categories query
        mode_categories = table.get_property('categories')
        if mode_categories == 'current_category':
            query_categorie = OrQuery(*[ PhraseQuery('categories', x)
                                         for x in categories ])
            query.append(query_categorie)
        elif mode_categories == 'one_category':
            query.append(PhraseQuery('categories',  table.get_property('specific_category')))
        # Show reductions ?
        promotion = table.get_property('show_product_with_promotion')
        if promotion == '0':
            query.append(PhraseQuery('has_reduction', False))
        elif promotion == '1':
            query.append(PhraseQuery('has_reduction', True))

        # Tags
        if table.get_property('tags'):
            query.append(
                OrQuery(*[PhraseQuery('tags', x)
                        for x in table.get_property('tags')]))

        # Selection in cross selling table
        handler = table.handler
        get_value = handler.get_record_value
        ids = list(handler.get_record_ids_in_order())
        names = []
        for id in ids[:products_quantity]:
            record = handler.get_record(id)
            path = get_value(record, 'name')
            names.append(path)
            products_quantity -= 1
            yield products_folder.get_resource(path)

        if products_quantity == 0:
            return
        query.append(
            NotQuery(
              OrQuery(*[ PhraseQuery('name', name) for name in names ])))

        # Complete results
        sort = table.get_property('sort')
        if sort == 'random':
            # Random selection
            results = root.search(AndQuery(*query))
            brains = list(results.get_documents())
            shuffle(brains)
            for brain in brains[:products_quantity]:
                yield root.get_resource(brain.abspath)
        elif sort == 'last':
            results = root.search(AndQuery(*query))
            brains = list(results.get_documents(sort_by='ctime',
                            reverse=True, size=products_quantity))
            for brain in brains:
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
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        target_name = Path(target).get_name()
        links = []

        handler = self.handler
        get_value = handler.get_record_value
        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            path = str(resolve_uri2(old_base, 'products/%s' % name))
            if path == source:
                handler.update_record(record.id, **{'name': target_name})
        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        site_root = self.get_site_root()
        target = self.get_canonical_path()

        handler = self.handler
        record_schema = handler.record_schema
        resources_old2new = get_context().database.resources_old2new
        get_value = handler.get_record_value
        for record in handler.get_records():
            path = get_value(record, 'name')
            if not path:
                continue
            ref = get_reference(str(path))
            if ref.scheme:
                continue
            path = ref.path
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Check if the target path has not been moved
            new_abs_path = resources_old2new.get(old_abs_path,
                                                 old_abs_path)
            new_name = new_abs_path.get_name()
            # Update the record
            handler.update_record(record.id, **{'name': new_name})


    def update_20090223(self):
        mode = self.get_property('mode')
        if self.get_property('use_shop_configuration') is False:
            if mode.startswith('last'):
                self.set_property('sort', 'last')
            else:
                self.set_property('sort', 'random')
            if mode.endwith('_category'):
                self.set_property('category', 'current_category')
            elif mode.endwith('_shop'):
                self.set_property('category', 'all_categories')
            self.set_property('show_product_with_promotion', '2')
        self.del_property('mode')


register_resource_class(CrossSellingTable)
