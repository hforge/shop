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
from itools.core import merge_dicts
from itools.datatypes import Integer, Boolean
from itools.gettext import MSG
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

    # TODO Add get_links, update_link


    @classmethod
    def get_metadata_schema(cls):
        schema = ResourcesOrderedTable.get_metadata_schema()
        schema['mode'] = CrossSelling_Modes
        schema['enabled'] = Boolean(default=False)
        schema['products_quantity'] = Integer(default=5)
        return schema


register_resource_class(CrossSellingTable)
