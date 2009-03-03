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

# Import from itools
from itools.datatypes import String
from itools.gettext import MSG
from itools.web import STLView

# Import from shop
from cart import ProductCart


class Cart_View(STLView):

    access = True
    title = MSG(u'View Cart')

    template = '/ui/cart/cart_view.xml'

    query_schema = {'action': String,
                    'product': String}

    def GET(self, resource, context):
        cart= ProductCart()
        action = context.query['action']
        if(action=='clear'):
            cart.clear()
        elif action in ['add', 'remove', 'delete']:
            product = context.get_form_value('product')
            product = resource.get_resource('products/%s' % product)
            if(action=='add'):
                cart.add_product(product.name)
            elif(action=='remove'):
                cart.remove_product(product.name)
            elif(action=='delete'):
                cart.delete_product(product.name)
        return STLView.GET(self, resource, context)


    def get_namespace(self, resource, context):
        namespace = {'products': []}
        # Get cart
        cart = ProductCart()
        # Get products
        products = resource.get_resource('products')
        # Get products informations
        total = 0
        for product in cart.get_elements():
            quantity = product['quantity']
            product = products.get_resource(product['name'])
            # Price
            price = 2#product.get_property('price')
            vat = 10#product.get_property('vat')
            price_after_vat = price + (price * vat/100)
            price_total = price_after_vat * int(quantity)
            # All
            product = ({'name': product.name,
                        'title': product.get_title(),
                        'uri': resource.get_pathto(product),
                        'quantity': quantity,
                        'price_before_vat': price,
                        'price_after_vat': price_after_vat,
                        'price_total': price_total,
                        })
            total = total + price_total
            namespace['products'].append(product)
        namespace['total'] = total
        return namespace
