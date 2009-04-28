# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from ikaaro
from ikaaro.registry import register_resource_class
from ikaaro.folder import Folder

# Import from itools
from itools.gettext import MSG

# Import from project
from addresses import Addresses
from categories import Categories
from orders import Orders
from payments import Payments
from products import Products, ProductModels
from shipping import Shippings
from shop_views import Shop_Buy, Shop_Delivery, Shop_RegisterProgress
from shop_views import Shop_View, Shop_ShowRecapitulatif, Shop_EditAddressProgress
from shop_views import Shop_RegisterProgress, Shop_AddAddressProgress
from shop_views import Shop_Addresses, Shop_ChooseAddress, Shop_End
from shop_views import Shop_ViewCart


class Shop(Folder):

    class_id = 'shop'
    class_title = MSG(u'Shop')
    class_views = ['view', 'view_cart']

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['addresses',
                          'categories', 'orders', 'payments',
                          'products', 'products-models',
                          'shippings']

    # Views
    view = Shop_View()


    # Views for payment processus
    # 1) View cart
    # 2) Login/Register
    # 3) Choose addreses
    # 4) Choose delivery
    # 5) Recapitulatif / payment
    # 6) Payment endt
    view_cart = Shop_ViewCart()
    register = Shop_RegisterProgress()
    addresses = Shop_Addresses()
    choose_address= Shop_ChooseAddress()
    edit_address = Shop_EditAddressProgress()
    add_address = Shop_AddAddressProgress()
    delivery = Shop_Delivery()
    show_recapitulatif = Shop_ShowRecapitulatif()
    buy = Shop_Buy()
    end = Shop_End()


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        root = Folder._make_resource(cls, folder, name, **kw)
        # Categories
        Categories._make_resource(Categories, folder, '%s/categories' % name,
                                title={'en': u'Categories'})
        # Payments module
        Payments._make_resource(Payments, folder, '%s/payments' % name,
                                title={'en': u'Payment module'})
        # Products
        Products._make_resource(Products, folder, '%s/products' % name,
                                title={'en': u'Products'})
        # Product Models
        ProductModels._make_resource(ProductModels, folder, '%s/products-models' % name,
                                    title={'en': u'Product Models'})
        # Orders
        Orders._make_resource(Orders, folder, '%s/orders' % name,
                              title={'en': u'Orders'})
        # Addresses
        Addresses._make_resource(Addresses, folder, '%s/addresses' % name,
                                 title={'en': u'Addresses'})
        # Shipping
        Shippings._make_resource(Shippings, folder, '%s/shippings' % name,
                                 title={'en': u'Shipping'})



    def get_document_types(self):
        return []


    def get_user_main_address(self, user_name):
        ns_addresses = []
        addresses = self.get_resource('addresses').handler
        for record in addresses.search(user=str(user_name)):
            return record
        return None


    def get_user_address(self, id):
        addresses = self.get_resource('addresses').handler
        record = addresses.get_record(id)
        ns = {}
        for key in ['firstname', 'lastname', 'address_1', 'address_2',
                    'zipcode', 'town', 'country', 'title', 'gender']:
            ns[key] = addresses.get_record_value(record, key)
        return ns


register_resource_class(Shop)
