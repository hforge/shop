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
from cart.cart_views import Cart_View #XXX
from orders import Orders
from payments import Payments
from products import Products, ProductModels
from shop_views import Shop_Buy, Shop_Register
from user import ShopUser


class View(STLView):

    access = 'is_admin'
    title = MSG(u'Test payment module')

    def GET(self, resource, context):
        payments = resource.get_resource('payments')
        payment = {'id': 'A250',
                  'price': 250.3,
                  'email': 'sylvain@itaapy.com',
                  'mode': 'paybox'}
        return payments.show_payment_form(context, payment)


class Shop(Folder):

    class_id = 'shop'
    class_title = MSG(u'Shop')
    class_views = Folder.class_views + ['test', 'view_cart']

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['orders', 'payments', 'products',
                          'products-models']

    # Views
    test = View()
    buy = Shop_Buy()
    register = Shop_Register()
    view_cart = Cart_View()

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



    def get_document_types(self):
        return []


register_resource_class(Shop)
