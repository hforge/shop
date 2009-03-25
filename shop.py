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
from itools.web import STLView

# Import from project
from addresses import Addresses
from cart.cart_views import Cart_View #XXX
from orders import Orders
from payments import Payments
from products import Products, ProductModels
from shop_views import Shop_Buy, Shop_Delivery, Shop_Register
from shop_views import Shop_View, Shop_ShowRecapitulatif, Shop_EditAddressForm
from user import ShopUser


class Shop(Folder):

    class_id = 'shop'
    class_title = MSG(u'Shop')
    class_views = ['view']

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['addresses', 'orders',
                          'payments', 'products', 'products-models']

    # Views
    view = Shop_View()
    view_cart = Cart_View()

    register = Shop_Register()
    edit_address = Shop_EditAddressForm()

    delivery = Shop_Delivery()
    show_recapitulatif = Shop_ShowRecapitulatif()
    buy = Shop_Buy()


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        root = Folder._make_resource(cls, folder, name, **kw)
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



    def get_document_types(self):
        return []


    def get_addresses_user(self, user_name):
        ns_addresses = []
        addresses = self.get_resource('addresses').handler
        for record in addresses.search(user=str(user_name)):
            kw = {}
            for key in ['address_1', 'address_2', 'zipcode',
                        'town', 'country']:
                kw[key] = addresses.get_record_value(record, key)
            ns_addresses.append(kw)
        return ns_addresses


register_resource_class(Shop)
