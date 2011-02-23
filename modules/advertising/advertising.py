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
from itools.core import merge_dicts
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import SelectWidget, MultilineWidget, XHTMLBody
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import Box, register_box
from itws.repository_views import Box_View
from itws.views import AutomaticEditView

# Import from shop
from shop.datatypes import DynamicEnumerate
from shop.folder import ShopFolder
from shop.modules import ShopModule

class DynamicProperty(dict):

    resource = None

    def __getitem__(self, key):
        ads = self.resource.get_resource(key, soft=True)
        if not ads:
            return u'This ads do not exist'
        return ads.get_property('code')


class Ads_List(DynamicEnumerate):

    format = 'shop_module_advertising_ad'
    is_abspath = True


class Advertising_SidebarBox_View(Box_View):

    def GET(self, resource, context):
        ads_abspath = resource.get_property('ads_abspath')
        if not ads_abspath:
            return None
        ads = context.root.get_resource(ads_abspath)
        return ads.get_property('code')


class Advertising_SidebarBox(Box):

    class_id = 'shop_module_advertising_sidebar_box'
    class_title = MSG(u'Box for advertising')
    class_description = MSG(u'Add an advertising on your sidebar')

    view = Advertising_SidebarBox_View()

    edit_schema = {'ads_abspath': Ads_List}

    edit_widgets = [
        SelectWidget('ads_abspath', title=MSG(u'Ads to show'),
            has_empty_option=False)]




class ShopModule_Advertising_Ad(ShopFolder):

    class_id = 'shop_module_advertising_ad'
    class_title = MSG(u'Advertising, an Ad')
    class_views = ['edit']

    edit = AutomaticEditView()

    edit_schema = {'code': XHTMLBody(sanitize_html=False)}
    edit_widgets = [MultilineWidget('code', title=MSG(u'Code'))]

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           cls.edit_schema)


class ShopModule_Advertising(ShopModule):

    class_id = 'shop_module_advertising'
    class_title = MSG(u'Advertising')
    class_views = ['browse_content']
    class_description = MSG(u'Advertising')

    def render(self, resource, context):
        d = DynamicProperty()
        d.resource = self
        return d


    def get_document_types(self):
        return [ShopModule_Advertising_Ad]


register_resource_class(ShopModule_Advertising)
register_box(Advertising_SidebarBox, allow_instanciation=True)
