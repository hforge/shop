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
from operator import itemgetter

# Import from itools
from itools.datatypes import String
from itools.gettext import MSG
from itools.stl import stl
from itools.web import STLView
from itools.xapian import PhraseQuery, AndQuery

# Import from ikaaro
from ikaaro.utils import get_base_path_query

# Import from shop
from utils import get_shop
from views import BrowseFormBatchNumeric


class VirtualCategory_BoxSubCategories(STLView):

    access = True
    template = '/ui/shop/virtualcategory_boxsubcategories.xml'


    def get_namespace(self, resource, context):
        root = context.root
        site_root = context.resource.get_site_root()

        # get the category
        namespace = {'title': resource.get_title(),
                     'description': resource.get_property('description'),
                     'sub_categories': []}

        # Get sub categories
        abspath = site_root.get_canonical_path()
        base_query = [
            get_base_path_query(str(abspath)),
            PhraseQuery('format', resource.virtual_product_class.class_id)]
        for subcat in resource.search_resources(format='category'):
            subcat_path = '%s/%s' % (resource.name, subcat.name)
            query = base_query + [PhraseQuery('categories', subcat_path)]
            query = AndQuery(*query)
            # Search inside the site_root
            results = root.search(query)
            nb_items = results.get_n_documents()
            if nb_items:
                namespace['sub_categories'].append(
                            {'title': subcat.get_title(),
                             'uri': context.get_link(subcat),
                             'nb_items': nb_items})

        # Sort by title
        namespace['sub_categories'].sort(key=itemgetter('title'))

        return namespace



class VirtualCategory_View(BrowseFormBatchNumeric):

    access = True
    title = MSG(u'View')

    search_template = None
    template = '/ui/shop/virtualcategory_view.xml'


    def get_namespace(self, resource, context):
        batch = None
        # Batch
        items = self.get_items(resource, context)
        if self.batch_template is not None:
            template = resource.get_resource(self.batch_template)
            namespace = self.get_batch_namespace(resource, context, items)
            batch = stl(template, namespace)
        items = self.sort_and_batch(resource, context, items)
        # Build namespace
        namespace = {'batch': batch,
                     'products': []}
        product_models = []
        for item_brain, item_resource in items:
            viewbox = item_resource.viewbox
            namespace['products'].append({'name': item_resource.name,
                                          'box': viewbox.GET(item_resource, context)})
        return namespace


    def get_items(self, resource, context):
        query = [
            PhraseQuery('format', resource.virtual_product_class.class_id),
            PhraseQuery('categories', resource.get_unique_id())]
        return context.root.search(AndQuery(*query))



class VirtualCategory_ComparatorView(VirtualCategory_View):

    access = True

    search_template = None
    template = '/ui/shop/virtualcategory_comparator_view.xml'


##########################################################
# Comparateur
##########################################################
class VirtualCategory_Comparator(STLView):

    access = True

    template = '/ui/shop/virtualcategory_comparator.xml'

    query_schema = {'products': String(multiple=True)}


    def get_namespace(self, resource, context):
        namespace = {'category': resource.get_title()}
        shop = get_shop(resource)
        # Check resources
        if len(context.query['products'])>3:
            return {'error': MSG(u'Too many products to compare')}
        if len(context.query['products'])<1:
            return {'error': MSG(u'Please select products to compare')}
        # Get real product resources
        products_to_compare = []
        products_models = []
        products = shop.get_resource('products')
        for product in context.query['products']:
            try:
                product_resource = products.get_resource(product)
            except LookupError:
                product_resource = None
            if not product_resource:
                return {'error': MSG(u'Error: product invalid')}
            products_to_compare.append(product_resource)
            product_model = product_resource.get_property('product_model')
            products_models.append(product_model)
        # Check if products models are the same
        if len(set(products_models))!=1:
            return {'error': MSG(u"You can't compare this products.")}
        # Build comparator namespace
        namespace['error'] = None
        namespace['products'] = []
        namespace['nb_products'] = len(products_to_compare)
        namespace['nb_products_plus_1'] = len(products_to_compare) +1
        abspath = shop.get_abspath()
        for product in products_to_compare:
            # Base products namespace
            ns = product.get_small_namespace(context)
            ns['href'] = abspath.get_pathto(product.get_virtual_path())
            namespace['products'].append(ns)
        # Comporator model schema
        model = products_to_compare[0].get_product_model()
        if model:
            model_ns = model.get_model_ns(products_to_compare[0])
            comparator = {}
            for key in model_ns['specific_dict'].keys():
                title = model_ns['specific_dict'][key]['title']
                comparator[key] = {'name': key,
                                   'title': title,
                                   'values': []}
            for product in products_to_compare:
                model_ns = model.get_model_ns(product)
                kw = []
                for key in model_ns['specific_dict'].keys():
                    value = model_ns['specific_dict'][key]['value']
                    comparator[key]['values'].append(value)
            namespace['comparator'] = comparator.values()
        return namespace
