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

# Import from itools
from itools.core import get_abspath
from itools.datatypes import Enumerate, Integer, Boolean
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.web import STLView
from itools.xmlfile import XMLFile

# Import from ikaaro
from ikaaro.forms import SelectWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule


class ShopModule_TwitterButton_View(STLView):

    access = True

    def get_template(self, resource, context):
        path = get_abspath('twitter.stl')
        return ro_database.get_handler(path, XMLFile)


    def get_namespace(self, resource, context):
        namespace = {'datacount': resource.get_property('datacount')}
        return namespace



class DataCount(Enumerate):

    options = [{'name': 'none', 'value': MSG(u'None')},
               {'name': 'vertical', 'value': MSG(u'Vertical')},
               {'name': 'horizontal', 'value': MSG(u'Horizontal')}]


class ShopModule_TwitterButton(ShopModule):

    class_id = 'shop_module_twitter_button'
    class_title = MSG(u'Twitter button')
    class_views = ['edit']
    class_description = MSG(u'Twitter button')

    item_schema = {'datacount': DataCount}

    item_widgets = [
        SelectWidget('datacount', title=MSG(u'Data count'), has_empty_option=False),
        ]


    def render(self, resource, context):
        return ShopModule_TwitterButton_View().GET(self, context)




register_resource_class(ShopModule_TwitterButton)
