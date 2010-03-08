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
from datetime import datetime

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import DateTime, String
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
                           owner=String,
                           ctime=DateTime,
                           data=XHTMLBody)


    @staticmethod
    def _make_resource(cls, folder, name, ctime=None, *args, **kw):
        if ctime is None:
            ctime = datetime.now()
        ShopFolder._make_resource(cls, folder, name, ctime=ctime, *args,
                                     **kw)


    def _get_catalog_values(self):
        return merge_dicts(ShopFolder._get_catalog_values(self),
                           ctime=self.get_property('ctime'))



class ShopModule_WishList(ShopFolder):

    class_id = 'shop-module-wishlist'
    class_title = MSG(u'Module wishlist')
    class_views = ['view', 'new_resource?type=wishlist',
                   'edit', 'browse_content']

    view = ShopModule_WishListView()
    edit = ShopModule_WishList_Edit()

    add_image = CurrentFolder_AddImage()

    def get_document_types(self):
        return [WishList]


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           data=XHTMLBody())


    def set_payment_as_ok(self, payment_way, id_record, context):
        """Payments module call this method when a payment is validated"""
        payments_table = payment_way.get_resource('payments').handler
        record = payments_table.get_record(id_record)
        ref = payments_table.get_record_value(record, 'ref')
        print ref, '@@@@@@@@'
        #order = shop.get_resource('orders/%s' % ref)
        # 3) Set order as payed (so generate bill)
        #order.set_as_payed(context)




register_resource_class(ShopModule_WishList)
