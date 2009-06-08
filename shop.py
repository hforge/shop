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
from itools.datatypes import Email, Unicode
from itools.gettext import MSG

# Import from project
from addresses import Addresses
from categories import Categories
from countries import Countries
from orders import Orders
from payments import Payments
from products import Products, ProductModels
from shipping import Shippings
from shop_views import Shop_Delivery, Shop_ViewCart, Shop_Configure
from shop_views import Shop_View, Shop_ShowRecapitulatif, Shop_EditAddressProgress
from shop_views import Shop_RegisterProgress, Shop_AddAddressProgress
from shop_views import Shop_Addresses, Shop_ChooseAddress


class Shop(Folder):

    class_id = 'shop'
    class_title = MSG(u'Shop')
    class_views = ['view', 'view_cart']
    class_version = '20090605'

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['addresses',
                          'categories', 'orders', 'payments',
                          'products', 'products-models',
                          'shippings', 'countries']


    ####################################
    ## Views
    ####################################

    # Administrator shop views
    view = Shop_View()
    configure = Shop_Configure()

    #------------------------------
    # 6 Steps for payment process
    #------------------------------

    # 1) View cart
    view_cart = Shop_ViewCart()

    # 2) Login/Register
    register = Shop_RegisterProgress()

    # 3) Choose/edit/add addresses
    addresses = Shop_Addresses()
    choose_address= Shop_ChooseAddress()
    edit_address = Shop_EditAddressProgress()
    add_address = Shop_AddAddressProgress()

    # 4) Choose delivery
    delivery = Shop_Delivery()

    # 5) Recapitulatif / payment
    show_recapitulatif = Shop_ShowRecapitulatif()

    # 6) Payment end (Define in payments views)


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
        # Countries
        Countries._make_resource(Countries, folder, '%s/countries' % name,
                                 title={'en': u'countries'})
        # Shipping
        Shippings._make_resource(Shippings, folder, '%s/shippings' % name,
                                 title={'en': u'Shipping'})


    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema['order_notification_mails'] = Email(multiple=True)
        schema['shop_signature'] = Unicode
        schema['shop_from_addr'] = Email
        return schema


    def get_document_types(self):
        return []

    ##############################
    # XXX To deplace
    ##############################

    def get_user_main_address(self, user_name):
        # TODO: user can define his default address
        ns_addresses = []
        addresses = self.get_resource('addresses').handler
        for record in addresses.search(user=str(user_name)):
            return record
        return None


    def get_user_address_namespace(self, id):
        addresses = self.get_resource('addresses').handler
        return addresses.get_record_namespace(id)


    ##############################
    # Updates
    ##############################

    def update_20090430(self):
        """ We add countries table """
        if self.get_resource('countries') is None:
            Countries._make_resource(Countries, self.handler, 'countries',
                                     **{'title': {'en': u'countries'}})


    def update_20090604(self):
        self.del_resource('shippings')
        self.del_resource('orders')
        self.del_resource('payments')


    def update_20090605(self):
        Shippings._make_resource(Shippings, self.handler, 'shippings',
                                  **{'title': {'en': u'Shippings'}})

        Orders._make_resource(Orders, self.handler, 'orders',
                                  **{'title': {'en': u'Orders'}})


        Payments._make_resource(Payments, self.handler, 'payments',
                                  **{'title': {'en': u'Payments'}})


register_resource_class(Shop)
