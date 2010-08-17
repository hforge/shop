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
from itools.csv import Table as BaseTable
from itools.datatypes import Enumerate, Integer, String
from itools.gettext import MSG
from itools.web import STLView, get_context

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.listeners import register_listener
from shop.modules import ShopModule
from shop.utils import get_skin_template


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


class ShopModule_Stock(ShopModule):

    class_id = 'shop_module_stock'
    class_title = MSG(u'Manage stock')
    class_views = ['view']
    class_description = MSG(u'Manage stock')


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
