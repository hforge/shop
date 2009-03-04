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

# Import from standard library
from datetime import datetime

# Import from itools
from itools.web import BaseView

# Import from shop
from cart import ProductCart
from orders import Order


class Shop_Buy(BaseView):

    access = True # XXX

    def POST(self, resource, context):
        order_ref = datetime.now().strftime('%y%m%d%M%S')
        client_mail = context.user.get_property('email')
        client_mail = 'sylvain@itaapy.com'
        # Step 1: Get products in the cart
        cart = ProductCart()
        products = []
        # Step 2: We create an order
        Order.make_resource(Order, resource, 'orders/%s' % order_ref,
                            title={'en': u'Order %s' % order_ref},
                            products=products)
        # Step 3: We clear the cart
        cart .clear()
        # Step 4: We show the payment form
        payment = {'id': order_ref,
                   'price': 250,
                   'email': client_mail,
                   'mode': 'paybox'}
        payments = resource.get_resource('payments')
        return payments.show_payment_form(context, payment)
