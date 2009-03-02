# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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
from ikaaro.root import Root as BaseRoot

# Import from itools
from itools.gettext import MSG
from itools.web import STLView

# Import from project
from payments import Payments
from products import Products, Product, ProductAttributes, ProductTypes
from cart.cart_views import Cart_View


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


class Root(BaseRoot):

    class_id = 'root'
    class_skin = 'ui/shop'
    class_title = MSG(u'root')
    class_views = BaseRoot.class_views + ['test', 'view_cart']

    __fixed_handlers__ = BaseRoot.__fixed_handlers__ + ['payments', 'products',
                          'types', 'attributes']

    # Views
    test = View()
    view_cart = Cart_View()

    @staticmethod
    def _make_resource(cls, folder, email, password):
        root = BaseRoot._make_resource(cls, folder, email, password)
        # Payments module
        Payments._make_resource(Payments, folder, 'payments',
                                title={'en': u'Payment module'})
        # Products
        Products._make_resource(Products, folder, 'products',
                                title={'en': u'Products'})
        # Product Attributes
        ProductAttributes._make_resource(ProductAttributes, folder, 'attributes',
                                         title={'en': u'Product attributes'})
        # Available Product Types
        ProductTypes._make_resource(ProductTypes, folder, 'types',
                                    title={'en': u'Product Types'})
        return root



###########################################################################
# Register
###########################################################################
register_resource_class(Root)
