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
from ikaaro.forms import XHTMLBody
from ikaaro.registry import register_resource_class

# Import from shop
from shop.utils import ShopFolder, CurrentFolder_AddImage

# Import from module
from wishlist_views import WishList_NewInstance
from wishlist_views import ShopModule_WishListView, ShopModule_WishList_Edit
from wishlist_views import WishList_View, WishList_Edit, WishList_Donate



class WishList(ShopFolder):

    class_id = 'wishlist'
    class_title = MSG(u'A wishlist')
    class_views = ['view', 'edit', 'donate']

    view = WishList_View()
    edit = WishList_Edit()
    donate = WishList_Donate()
    new_instance = WishList_NewInstance()

    add_image = CurrentFolder_AddImage()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           data=XHTMLBody())




class ShopModule_WishList(ShopFolder):

    class_id = 'shop-module-wishlist'
    class_title = MSG(u'Module wishlist')
    class_views = ['view', 'edit', 'browse_content']

    view = ShopModule_WishListView()
    edit = ShopModule_WishList_Edit()

    add_image = CurrentFolder_AddImage()

    def get_document_types(self):
        return [WishList]


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           data=XHTMLBody())


register_resource_class(ShopModule_WishList)
