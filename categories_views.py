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
from itools.stl import stl
from itools.web import STLView
from itools.xapian import PhraseQuery, AndQuery

# Import from ikaaro
from ikaaro.utils import get_base_path_query

# Import from shop
from views import BrowseFormBatchNumeric


class VirualCategory_BoxSubCategories(STLView):

    access = True
    template = '/ui/shop/virtualcategorie_boxsubcategories.xml'


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
            PhraseQuery('format', 'product')]
        for subcat in resource.search_resources(format='categorie'):
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



class VirualCategory_View(BrowseFormBatchNumeric):

    access = True

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
        for item in items:
            ns = item.get_small_namespace(context)
            product_models.append(item.get_property('product_model'))
            namespace['products'].append(ns)
        namespace['can_compare'] = len(set(product_models)) == 1
        return namespace


    def get_items(self, resource, context):
        query = [
            PhraseQuery('format', 'product'),
            PhraseQuery('categories', resource.get_unique_id())]
        return context.root.search(AndQuery(*query))
