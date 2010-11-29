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
from ikaaro.forms import BooleanRadio, SelectWidget, TextWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.modules import ShopModule


class Layout(Enumerate):

    options = [{'name': 'standard', 'value': MSG(u'Standard')},
               {'name': 'button_count', 'value': MSG(u'Button count')}]


class Action(Enumerate):

    options = [{'name': 'like', 'value': MSG(u'Like')},
               {'name': 'recommand', 'value': MSG(u'Recommand')}]


class ColorScheme(Enumerate):

    options = [{'name': 'light', 'value': MSG(u'Light')},
               {'name': 'dark', 'value': MSG(u'Dark')}]


class ShopModule_FacebookLike_View(STLView):

    access = True

    def get_template(self, resource, context):
        path = get_abspath('facebook_like.stl')
        return ro_database.get_handler(path, XMLFile)


    def get_namespace(self, resource, context):
        uri = context.uri
        uri.query = {}
        namespace = {'uri': uri}
        for key in resource.item_schema.keys():
            namespace[key] = resource.get_property(key)
        return namespace



class ShopModule_FacebookLike(ShopModule):

    class_id = 'shop_module_facebook_like'
    class_title = MSG(u'Facebook like')
    class_views = ['edit']
    class_description = MSG(u'Facebook like')

    item_schema = {'layout': Layout,
                   'the_action': Action,
                   'width': Integer,
                   'height': Integer,
                   'colorscheme': ColorScheme,
                   'show_faces': Boolean}

    item_widgets = [
        SelectWidget('layout', title=MSG(u'Layout'), has_empty_option=False),
        SelectWidget('the_action', title=MSG(u'Action'), has_empty_option=False),
        SelectWidget('colorscheme', title=MSG(u'Color Scheme'), has_empty_option=False),
        TextWidget('width', title=MSG(u'Width (px)')),
        TextWidget('height', title=MSG(u'Height (px)')),
        BooleanRadio('show_faces', title=MSG(u'Show faces ?'))]


    def render(self, resource, context):
        return ShopModule_FacebookLike_View().GET(self, context)




register_resource_class(ShopModule_FacebookLike)
