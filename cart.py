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

# Import from itools
from itools.web import get_context

# Import from ikaaro
from ikaaro.datatypes import Password


class ProductCart(object):
    """
    A cart contains 3 informations
      -> Products name / quantity / options
      -> Delivery mode name
      -> Addresses id
    """

    def __init__(self, context):
        self.context = context
        # Init cookies
        for key in ['products', 'addresses', 'shipping']:
            if not self.context.has_cookie(key):
                self.context.set_cookie(key, '', path='/')
        # We load cart
        self.products = self._get_products()
        self.addresses = self._get_addresses()
        self.shipping = self._get_shipping()


    ######################
    # Namespace
    ######################

    def get_namespace(self):
        return {'nb_products': self.get_nb_products()}


    #######################################
    ## Products
    #######################################
    def _get_products(self):
        """
        Format of cookie "products":
          id|name|quantity|option:value#option:value
        Example:
          1|polo-red-ikaaro|2|color:rouge#size:M
        """
        products = []
        cookie = self.context.get_cookie('products')
        if not cookie:
            return products
        cookie = Password.decode(cookie)
        for data in cookie.split('@'):
            id, name, quantity, data_options = data.split('|')
            options = {}
            if data_options:
                for option in data_options.split('#'):
                    key, value = option.split(':')
                    options[key] = value
            products.append({'id': id,
                             'name': name,
                             'quantity': int(quantity),
                             'options': options})
        return products


    def save_products(self):
        cookies = []
        for product in self.products:
            options = '#'.join(['%s:%s' % (x, y)  for x, y in product['options'].items()])
            cookie = '%s|%s|%s|%s' % (product['id'], product['name'],
                                      product['quantity'], options)
            cookies.append(cookie)
        products = Password.encode('@'.join(cookies))
        context = get_context()
        context.set_cookie('products', products, path='/')



    def manage_product(self, id, quantity=0, options={}, name=None):
        for product in self.products:
            # Product already in cart
            if(product['id']==id):
                product['quantity'] = int(product['quantity'])
                new_quantity = product['quantity'] + quantity
                if new_quantity == 0:
                    # Remove the product
                    self.products.remove(product)
                else:
                    product['quantity'] = new_quantity
                self.save_products()
                return
            # Product not in cart
            if(product['name']==name):
                if product['options']==options:
                    new_quantity = product['quantity'] + quantity
                    if new_quantity == 0:
                        # Remove the product
                        self.products.remove(product)
                    else:
                        product['quantity'] = new_quantity
                    self.save_products()
                    return
        id = len(self.products)
        self.products.append({'id': id,
                              'name': name,
                              'quantity': quantity,
                              'options': options})
        self.save_products()
        return


    def add_product(self, name, quantity=1, options={}):
        self.manage_product(None, quantity, options, name)


    def add_a_product(self, id, quantity=1, options={}):
        self.manage_product(id, quantity, options)


    def remove_a_product(self, id, quantity=-1, options={}):
        self.manage_product(id, quantity, options)


    def delete_a_product(self, id):
        for product in self.products:
            if(product['id']==id):
                self.products.remove(product)
                break
        self.save_products()


    def get_nb_products(self):
        nb_products = 0
        for product in self.products:
            nb_products += product['quantity']
        return nb_products


    ######################
    # Shipping
    ######################

    def _get_shipping(self):
        """
        Format of cookie "shipping":
          shipping_name|shipping_option
        Example:
          collisimo|suivi
        """
        cookie = self.context.get_cookie('shipping')
        if not cookie:
            return None
        cookie = Password.decode(cookie)
        name, option = cookie.split('|')
        return {'name': name, 'option': option}


    def set_shipping(self, shipping_name, shipping_option=''):
        value = Password.encode('%s|%s' % (shipping_name, shipping_option))
        cookie = self.context.set_cookie('shipping', value)


#    def get_shipping(self):
#        return self.shipping['name']
#
#
#    def get_shipping_option(self):
#        return self.shipping['option']

    ######################
    # Addresses
    ######################

    def _get_addresses(self):
        """
        Format of cookie "addresses":
          id_delivery_address|id_bill_address
        Example:
          25|45
        """
        cookie = self.context.get_cookie('addresses')
        if not cookie:
            delivery_address = bill_address = None
        else:
            cookie = Password.decode(cookie)
            delivery_address, bill_address = cookie.split('|')
            delivery_address = int(delivery_address) if delivery_address else None
            bill_address = int(bill_address) if bill_address else None
        return {'delivery_address':delivery_address,
                'bill_address': bill_address}


    def _set_addresses(self, delivery_address, bill_address):
        if delivery_address==None:
            delivery_address = ''
        if bill_address==None:
            bill_address = ''
        value = Password.encode('%s|%s' % (delivery_address, bill_address))
        context = get_context()
        context.set_cookie('addresses', value)


    def set_delivery_address(self, id):
        self._set_addresses(id, self.addresses['bill_address'])


    def set_bill_address(self, id):
        self._set_addresses(id, self.addresses['delivery_address'])


#    def get_delivery_address(self):
#        return self.addresses['delivery_address']
#
#
#    def get_bill_address(self):
#        return self.addresses['bill_address']


    ######################
    # Check validity
    ######################

    def is_valid(self):
        """
        To be valid a cart must contains:
          - shipping id, addresses id, products
        """
        return (self.shipping['name'] is not None and
                len(self.products) > 0 and
                self.addresses['delivery_address'] is not None and
                self.addresses['bill_address'] is not None)

    def clear(self):
        for key in ['products', 'addresses', 'shipping']:
            self.context.del_cookie(key)


    def clean(self):
        for key in ['addresses', 'shipping']:
            self.context.del_cookie(key)