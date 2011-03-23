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
from itools.log import log_warning
from itools.xapian import OrQuery, AndQuery, PhraseQuery, NotQuery

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.future.order import ResourcesOrderedTableFile
from ikaaro.registry import register_resource_class

# Import from shop
from cross_selling_views import AddProduct_View
from cross_selling_views import CrossSelling_Configure, CrossSelling_TableView
from cross_selling_views import CrossSelling_Edit, cross_selling_schema
from utils import get_group_name, get_shop
from forms import ProductSelectorWidget
from products import Product




class CrossSellingTable(ResourcesOrderedTable):

    class_id = 'CrossSellingTable'
    class_title = MSG(u'Cross-Selling Table')
    class_description = MSG(u'This box allow to configure cross selling')
    class_handler = ResourcesOrderedTableFile
    class_version = '20100928'
    class_views = ['configure', 'back']

    form = [ProductSelectorWidget('name', title=MSG(u'Product'))]

    orderable_classes = Product

    # Views
    configure = CrossSelling_Configure()
    edit = CrossSelling_Edit()
    view_table = CrossSelling_TableView()
    add_product = AddProduct_View() # (XXX used by product selector widget)
    back = GoToSpecificDocument(specific_document='..',
                                title=MSG(u'See product'))

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ResourcesOrderedTable.get_metadata_schema(),
                           cross_selling_schema)


    def get_order_root(self):
        return self


    def get_products(self, context, product_format,
                     categories=[], excluded_products=[]):
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
                 PhraseQuery('workflow_state', 'public')]
        # Do not show now buyable products
        group_name = get_group_name(shop, context)
        q = PhraseQuery('not_buyable_by_groups', group_name)
        query.append(NotQuery(q))
        # Excluded products query
        if excluded_products:
            exclude_query = [ PhraseQuery('abspath', str(abspath))
                              for abspath in excluded_products ]
            if len(exclude_query) > 1:
                exclude_query = OrQuery(*exclude_query)
            else:
                exclude_query = exclude_query[0]
            query.append(NotQuery(exclude_query))
        # Filter on product title
        filter_text = table.get_property('filter_text')
        if filter_text:
            query.append(PhraseQuery('title', filter_text))
        # Categories query
        mode_categories = table.get_property('categories')
        if mode_categories == 'current_category':
            query_categorie = OrQuery(
                    *[ PhraseQuery('parent_paths', str(x.get_abspath()))
                        for x in categories ])
            query.append(query_categorie)
        elif mode_categories == 'one_category':
            query.append(PhraseQuery('parent_paths', table.get_property('specific_category')))
        # Show reductions ?
        promotion = table.get_property('show_product_with_promotion')
        if promotion in ('0', '1'):
            query.append(PhraseQuery('has_reduction', bool(promotion)))

        # Product model
        product_model = table.get_property('product_model')
        if product_model:
            query.append(PhraseQuery('product_model', product_model))
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
            resource = self.get_resource(path, soft=True)
            if resource is None:
                log_warning('Error cross selling, %s' % path)
            elif resource.get_property('state') == 'public':
                yield resource

        if products_quantity <= 0:
            return

        if names:
            names_query = [ PhraseQuery('name', name) for name in names ]
            if len(names_query) > 1:
                names_query = OrQuery(*names_query)
            else:
                names_query = names_query[0]
            query.append(NotQuery(names_query))

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



register_resource_class(CrossSellingTable)
