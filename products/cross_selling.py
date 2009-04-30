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
from ikaaro.forms import TextWidget, stl_namespaces
from ikaaro.future.order import ResourcesOrderedTableFile
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTable
from ikaaro.table_views import OrderedTable_View

# Import from shop
from cross_selling_views import AddProduct_View



class ProductSelectorWidget(TextWidget):

    method_to_call = 'add_product'
    template = list(XMLParser(
    """
    <input type="text" id="selector_${name}" size="${size}" name="${name}"
      value="${value}" />
    <input id="selector_button_${name}" type="button" value="..."
      name="selector_button_${name}"
      onclick="popup(';${method}?target_id=selector_${name}', 620, 300);"/>
    """, stl_namespaces))


    def get_namespace(self, datatype, value):
        namespace = TextWidget.get_namespace(self, datatype, value)
        namespace['method'] = self.method_to_call
        return namespace



class ResourcesOrderedTable_Ordered(OrderedTable_View):

    thumb_size = (50, 50)


    def get_table_columns(self, resource, context):
        return [('checkbox', None),
                ('id', MSG(u'id')),
                ('title', MSG(u'Title')),
                ('description', MSG(u'Description')),
                ('image', MSG(u'Image')),
                ('order', MSG(u'Order'))]


    def get_item_value(self, resource, context, item, column):
        if column in ('title', 'description', 'image'):
            real_resource = resource.get_real_resource()
            categories = real_resource.parent.parent
            try:
                product = categories.get_resource(item.name)
            except LookupError:
                product = None
        if column == 'title':
            if product is None:
                return item.name
            handler = resource.handler
            value = handler.get_record_value(item, column)
            # FIXME FO or BO link ?
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
    class_views = ['view', 'add_record']

    form = [ProductSelectorWidget('name', title=MSG(u'Product'))]

    # Views
    view = ResourcesOrderedTable_Ordered()
    add_product = AddProduct_View()
    # TODO Add get_links, update_link



register_resource_class(CrossSellingTable)
