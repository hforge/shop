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

# Import from the Standard Library

# Import from itools
from itools.web import get_context


class ProductCart(object):
    """
    A cart contains 3 informations
      -> Products name / quantity
      -> Delivery mode name
      -> Addresses id
    """



    def __init__(self):
        context = get_context()
        if not context.has_cookie('cart'):
            context.set_cookie('cart', '')
        if not context.has_cookie('shipping'):
            context.set_cookie('shipping', '')


    def get_elements(self):
        """
        Transform an cookie value (str) as:
          name:product1|quantity:2@name:product2|quantity:3
        in a list of dictionnaty as:
          [{'name': 'product1',
            'quantity': 2},
           {'name': 'product2',
            'quantity': 3}]
        """
        cart = get_context().get_cookie('cart')
        if not cart:
            return []
        l = []
        for elt in cart.split('@'):
            kw = {}
            for info in elt.split('|'):
                key, value = info.split(':')
                kw[key] = value
            l.append(kw)
        return l


    def set_cart(self, elements):
        """This method transform a list of dict as
          [{'name': 'product1',
            'quantity': 2},
           {'name': 'product2',
            'quantity': 3}]
        in a str as :
          name:product1|quantity:2@name:product2|quantity:3
        """
        context = get_context()
        l = []
        for elt in elements:
            l.append('|'.join(['%s:%s' % (x, y) for x, y in elt.items()]))
        context.set_cookie('cart', '@'.join(l))


    def clear(self):
        self.set_cart([])

    ######################
    # Products
    ######################

    def manage_product(self, name, quantity=0):
        context = get_context()
        # Check if product already in cart
        products = self.get_elements()
        for i, product in enumerate(products):
            if(product['name']==name):
                product['quantity'] = int(product['quantity'])
                new_quantity = product['quantity'] + quantity
                if new_quantity == 0:
                    # Remove the product
                    products.remove(product)
                else:
                    product['quantity'] += quantity
                    products[i] = product
                self.set_cart(products)
                return
        # You can only remove product already in cart
        if quantity < 0:
            return
        # Product not in cart
        products.append({'name': name,
                         'quantity': quantity})
        self.set_cart(products)


    def add_product(self, name, quantity=1):
        self.manage_product(name, quantity)


    def remove_product(self, name, quantity=-1):
        self.manage_product(name, quantity)


    def delete_product(self, name):
        context = get_context()
        products = self.get_elements()
        # Check if product already in cart
        for i, product in enumerate(products):
            if(product['name']==name):
                products.remove(products[i])
                break
        self.set_list_products(products)


    def get_total_price(self, products):
        price = 0.0
        for product_cart in self.get_elements():
            product = products.get_resource(product_cart['name'])
            # Check product is buyable
            if not product.is_buyable():
                continue
            # Calcul price
            quantity = product_cart['quantity']
            price = product.get_price() * int(quantity)
        return price

    ######################
    # Shipping
    ######################

    def set_shipping(self, mode):
        context = get_context()
        context.set_cookie('shipping', mode)


    def get_shipping(self):
        context = get_context()
        return context.get_cookie('shipping')

    ######################
    # Set addresses
    ######################

    def set_delivery_address(self, id):
        context = get_context()
        context.set_cookie('delivery_address', id)


    def get_delivery_address(self):
        context = get_context()
        address = context.get_cookie('delivery_address')
        if address is None:
            return None
        return int(address)


    def set_bill_address(self, id):
        context = get_context()
        id_delivery = context.get_cookie('delivery_address')
        if str(id_delivery)==str(id):
            context.del_cookie('bill_address')
        else:
            context.set_cookie('bill_address', id)


    def get_bill_address(self):
        context = get_context()
        address = context.get_cookie('bill_address')
        if address is None:
            return None
        return int(address)

    ######################
    # Check validity
    ######################

    def is_valid(self):
        """
        To be valid a cart must contains:
          - shipping id, addresses id, products
        """
        return (bool(self.get_shipping()) and
                bool(self.get_elements()) and
                bool(self.get_delivery_address()))
