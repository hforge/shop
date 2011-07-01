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
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.web import STLView
from itools.xmlfile import XMLFile

# Import from ikaaro
from ikaaro.forms import SelectWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule


class ShopModule_GooglePlusOneButton_View(STLView):

    access = True

    def get_template(self, resource, context):
        path = get_abspath('plusone.stl')
        return ro_database.get_handler(path, XMLFile)


    def get_namespace(self, resource, context):
        namespace = {}
        for key in ['size', 'count']:
            namespace[key] = resource.get_property(key)
        return namespace



class Size(Enumerate):

    options = [{'name': 'small', 'value': MSG(u'Small')},
               {'name': 'medium', 'value': MSG(u'Medium')},
               {'name': 'standard', 'value': MSG(u'Standard')},
               {'name': 'tall', 'value': MSG(u'Tall')}]


class Count(Enumerate):

    options = [{'name': 'true', 'value': MSG(u'True')},
               {'name': 'false', 'value': MSG(u'False')}]


class ShopModule_GooglePlusOneButton(ShopModule):

    class_id = 'shop_module_google_plus_one'
    class_title = MSG(u'Google plus one button')
    class_views = ['edit']
    class_description = MSG(u'Google plus one button')

    item_schema = {'size': Size,
                   'count': Count}

    item_widgets = [
        SelectWidget('size', title=MSG(u'Size'), has_empty_option=False),
        SelectWidget('count', title=MSG(u'Show count ?'), has_empty_option=False),
        ]


    def render(self, resource, context):
        return ShopModule_GooglePlusOneButton_View().GET(self, context)



register_resource_class(ShopModule_GooglePlusOneButton)
