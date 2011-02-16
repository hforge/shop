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
from itools.datatypes import Enumerate, String
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.web import STLView
from itools.xmlfile import XMLFile

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule


class AddThis_Styles(Enumerate):

    options = [
        {'name': '1', 'value': MSG(u'Style 1')},
        {'name': '2', 'value': MSG(u'Style 2')},
        {'name': '3', 'value': MSG(u'Style 3')},
        {'name': '4', 'value': MSG(u'Style 4')},
        {'name': '5', 'value': MSG(u'Style 5')},
        {'name': '6', 'value': MSG(u'Style 6')}]


class ShopModule_AddThis_View(STLView):

    access = True

    def get_template(self, resource, context):
        style = resource.get_property('style')
        path = get_abspath('addthis_%s.stl' % style)
        return ro_database.get_handler(path, XMLFile)


    def get_namespace(self, resource, context):
        languages = context.site_root.get_property('website_languages')
        lang = context.accept_language.select_language(languages)
        return {'lang': lang,
                'username': resource.get_property('username') or ''}



class ShopModule_AddThis(ShopModule):

    class_id = 'shop_module_addthis'
    class_title = MSG(u'Add This')
    class_views = ['edit']
    class_description = MSG(u'Add this')

    item_schema = {'username': String,
                   'style': AddThis_Styles(default=1)}

    item_widgets = [TextWidget('username', title=MSG(u'Addthis account username')),
                    SelectWidget('style', title=MSG(u'Style'), has_empty_option=False)]


    def render(self, resource, context):
        return ShopModule_AddThis_View().GET(self, context)



register_resource_class(ShopModule_AddThis)
