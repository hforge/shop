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
from itools.web import get_context

# Import from ikaaro
from ikaaro.access import AccessControl
from ikaaro.forms import XHTMLBody
from ikaaro.registry import register_resource_class

# Import from shop
from shop.folder import ShopFolder
from shop.utils import CurrentFolder_AddImage

# Import from module
from wishlist_views import WishList_NewInstance
from wishlist_views import ShopModule_WishListView, ShopModule_WishList_Edit
from wishlist_views import WishList_View, WishList_Edit, WishList_Donate
from wishlist_views import ShopModule_WishList_PaymentsEndViewTop
from shop.payments.credit import CreditPayment
from shop.utils import get_shop



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
        context = get_context()
        kw['owner'] = context.user.name
        ShopFolder._make_resource(cls, folder, name, ctime=ctime, *args,
                                     **kw)


    def _get_catalog_values(self):
        return merge_dicts(ShopFolder._get_catalog_values(self),
                           ctime=self.get_property('ctime'))



class ShopModule_WishList(AccessControl, ShopFolder):

    class_id = 'shop-module-wishlist'
    class_title = MSG(u'Module wishlist')
    class_views = ['view', 'new_resource?type=wishlist',
                   'edit', 'browse_content']

    view = ShopModule_WishListView()
    edit = ShopModule_WishList_Edit()

    add_image = CurrentFolder_AddImage()
    end_view_top = ShopModule_WishList_PaymentsEndViewTop()

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
        # Get amount of gift
        amount = payments_table.get_record_value(record, 'amount')
        # Get wishlist
        ref = payments_table.get_record_value(record, 'ref')
        # Get name of user that made the gift
        user_made_gift = payments_table.get_record_value(record, 'user')
        # Get wishlist oner to credit money
        wishlist = self.get_resource(ref)
        owner = wishlist.get_property('owner')
        # Create a descript
        description = MSG(u'Gift made by user {user_name} ({user_title})')
        description = description.gettext(user_name=user_made_gift,
                          user_title=context.root.get_user_title(owner))
        # Add amount to credit available for user
        payments = get_shop(context.resource).get_resource('payments')
        credit_payment_way = list(payments.search_resources(cls=CreditPayment))[0]
        users_credit = credit_payment_way.get_resource('users-credit')
        users_credit.add_new_record({'user': owner,
                                     'amount': amount,
                                     'description': description})


    #############################
    # ACL
    #############################
    def is_allowed_to_view(self, user, resource):
        is_invited = False
        is_owner_or_admin = self.is_owner_or_admin(user, resource)
        return is_owner_or_admin or is_invited


    def is_owner_or_admin(self, user, resource):
        if not user:
            return False
        # Admins are all powerfull
        #if self.is_admin(user, resource):
        #    return True
        owner = resource.get_property('owner')
        return owner == user.name


register_resource_class(ShopModule_WishList)
