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

# Import from itools
from itools.gettext import MSG
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import PathSelectorWidget
from ikaaro.future.order import ResourcesOrderedTableFile
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTable
from ikaaro.table_views import OrderedTable_View

# Import from shop
from cross_selling_views import AddLinkCrossSelling



class ResourcesOrderedTable_Ordered(OrderedTable_View):

    thumb_size = (50, 50)

    def get_table_columns(self, resource, context):
        columns = [('checkbox', None),
                   ('id', MSG(u'id')),
                   ('title', MSG(u'Title')),
                   ('description', MSG(u'Description')),
                   ('image', MSG(u'Image')),
                   ('order', MSG(u'Order'))]
        return columns


    def get_item_value(self, resource, context, item, column):
        if column in ('title', 'description', 'image'):
            try:
                product = resource.get_resource(item.name)
            except LookupError:
                product = None
        if column == 'title':
            if product is None:
                return item.name
            handler = resource.handler
            value = handler.get_record_value(item, column)
            return product.get_title(), context.get_link(product)
        elif column == 'description':
            if product is None:
                return None
        elif column == 'image':
            if product is None:
                return None
            ns = product.get_cover_namespace(context)
            if ns:
                width, height = self.thumb_size
                tpl = '<img src="%s/;thumb?width=%s&amp;height=%s" />'
                return XMLParser(tpl % (ns['href'], width, height))
            return None
        return OrderedTable_View.get_item_value(self, resource, context, item,
                                                column)



class CrossSellingTable(OrderedTable):

    class_id = 'CrossSellingTable'
    class_title = MSG(u'Cross-Selling Table')
    class_handler = ResourcesOrderedTableFile

    form = [PathSelectorWidget('name', title=MSG(u'Product'))]

    # Views
    view = ResourcesOrderedTable_Ordered()
    add_link = AddLinkCrossSelling()
    # TODO Add get_links, update_link


    def get_add_selected_classes(self, add_type, target_id):
        if add_type == 'add_link' and target_id == 'name':
            from product import Product
            return [Product]
        return OrderedTable.get_add_selected_classes(self, add_type,
                                                     target_id)


    def get_add_bc_root(self, add_type, target_id):
        return self.get_real_resource().parent.parent



register_resource_class(CrossSellingTable)
