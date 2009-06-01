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
from itools.stl import stl
from itools.xapian import PhraseQuery, AndQuery

# Import from shop
from views import BrowseFormBatchNumeric


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
