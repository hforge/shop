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
from shop.shop_views import Shop_Progress
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
        abspath = resource.get_abspath()
        namespace = {'products': []}
        # Get cart
        cart = ProductCart()
        # Get products
        products = resource.get_resource('products')
        # Get products informations
        total = 0
        for product_cart in cart.get_elements():
            # Get product
            product = products.get_resource(product_cart['name'])
            # Check product is buyable
            if not product.is_buyable():
                continue
            # Calcul price
            quantity = product_cart['quantity']
            price = product.get_price()
            price_total = price * int(quantity)
            # All
            ns = ({'name': product.name,
                   'img': product.get_cover_namespace(context),
                   'title': product.get_title(),
                   'href': abspath.get_pathto(product.get_virtual_path()),
                   'quantity': quantity,
                   'price': price,
                   'price_total': price_total})
            total = total + price_total
            namespace['products'].append(ns)
        namespace['total'] = total
        # Progress bar
        namespace['progress'] = Shop_Progress(index=1).GET(resource, context)
        return namespace
