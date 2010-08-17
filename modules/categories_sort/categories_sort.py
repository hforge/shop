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

# Import from itools
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.web import STLView, get_context

# Import from ikaaro
from ikaaro.forms import SelectWidget

# Import from shop
from shop.modules import ShopModule
from shop.utils import get_skin_template


class CategoriesSortEnumerate(Enumerate):

    values = [('stored_price', '0', MSG(u'Price: lowest first')),
              ('stored_price', '1', MSG(u'Price: highest first')),
              ('title', '0', MSG(u'Name: A to Z')),
              ('title', '1', MSG(u'Name: Z to A'))]

    @classmethod
    def get_options(cls):
        context = get_context()
        options = []
        for sort_by, reverse, value in cls.values:
            uri = deepcopy(context.uri)
            uri.query['sort_by'] = sort_by
            uri.query['reverse'] = reverse
            options.append(
                {'name': str(uri),
                 'value': value})
        return options




class ShopModule_CategoriesSortView(STLView):

    def get_template(self, resource, context):
        return get_skin_template(context, '/modules/categories_sort.xml')


    def get_namespace(self, resource, context):
        datatype = CategoriesSortEnumerate
        value = str(context.uri)
        widget = SelectWidget('sort_by', has_empty_option=False)
        return {'widget': widget.to_html(datatype, value)}



class ShopModule_CategoriesSort(ShopModule):

    class_id = 'shop_module_categories_sort'
    class_title = MSG(u'Categories Sort')
    class_views = ['view']
    class_description = MSG(u'Categories Sort')

    def render(self, resource, context):
        return ShopModule_CategoriesSortView().GET(resource, context)
