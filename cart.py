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
from decimal import Decimal as decimal

# Import from itools
from itools.web import get_context

# Import from ikaaro
from ikaaro.datatypes import Password

# Import from shop
from utils import format_price
from utils import get_shippings_details


class ProductCart(object):
    """
    A cart contains 4 informations
      -> Products name / quantity / declination
      -> Delivery mode name
      -> Addresses id
      -> Delivery zone ID
    """

    def __init__(self, context):
        self.context = context
        # Init cookies
        for key in ['products', 'addresses', 'shipping']:
            if self.context.get_cookie(key) is None:
                self.context.set_cookie(key, '', path='/')
        # We load cart
        self.products = self._get_products()
        self.addresses = self._get_addresses()
        self.shipping = self._get_shipping()
        self.id_zone = self._get_id_zone()


    ######################
    # Namespace
    ######################

    def get_namespace(self, resource):
        context = self.context
        abspath = resource.get_abspath()
        # products namespace
        products_ns = []
        total_with_tax = decimal(0)
        total_pre_tax = decimal(0)
        for product_cart in self.products:
            # Get product
            product = context.root.get_resource(product_cart['name'], soft=True)
            # Check product is buyable
            if not product or not product.is_buyable(context):
                continue
            quantity = product_cart['quantity']
            id_declination = product_cart['declination']
            unit_price_with_tax = product.get_price_with_tax(id_declination)
            unit_price_with_tax = decimal(unit_price_with_tax)
            total_with_tax += unit_price_with_tax * quantity
            unit_price_pre_tax = product.get_price_without_tax(id_declination)
            unit_price_pre_tax = decimal(unit_price_pre_tax)
            total_pre_tax += unit_price_pre_tax * quantity

            product_ns = {'id': product_cart['id'],
                          'name': product.name,
                          'title': product.get_title(),
                          'href': context.get_link(product),
                          'price': unit_price_with_tax * quantity,
                          'quantity': quantity}
            products_ns.append(product_ns)
        # Build namespace
        return {'nb_products': self.get_nb_products(),
                'total_with_tax': format_price(total_with_tax),
                'total_pre_tax': format_price(total_pre_tax),
                'products': products_ns}

    #######################################
    ## Products
    #######################################
    def _get_products(self):
        """
        Format of cookie "products":
          id|name|quantity|declination
        Example:
          1|polo-red-ikaaro|2|4
        """
        products = []
        cookie = self.context.get_cookie('products')
        if not cookie or cookie == 'deleted':
            return products
        cookie = Password.decode(cookie)
        for data in cookie.split('@'):
            id, name, quantity, declination = data.split('|')
            # Check product exist
            product = self.context.root.get_resource(name, soft=True)
            if not product or not product.is_buyable(self.context):
                continue
            # Add product
            products.append({'id': id,
                             'name': name,
                             'quantity': int(quantity),
                             'declination': declination})
        return products


    def save_products(self):
        cookies = []
        for product in self.products:
            cookie = '%s|%s|%s|%s' % (product['id'], product['name'],
                                      product['quantity'], product['declination'] or '')
            cookies.append(cookie)
        products = Password.encode('@'.join(cookies))
        context = get_context()
        context.set_cookie('products', products, path='/')



    def manage_product(self, id, quantity=0, declination=None, name=None):
        for product in self.products:
            # Product already in cart
            if(product['id'] == id):
                product['quantity'] = int(product['quantity'])
                new_quantity = product['quantity'] + quantity
                if new_quantity <= 0:
                    # Remove the product
                    self.products.remove(product)
                else:
                    product['quantity'] = new_quantity
                self.save_products()
                return
            # Product not in cart
            if(product['name'] == name):
                if product['declination'] == declination:
                    new_quantity = product['quantity'] + quantity
                    if new_quantity <= 0:
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
                              'declination': declination})
        self.save_products()
        return


    def add_product(self, product, quantity=1, declination=None):
        self.manage_product(None, quantity, declination, product.get_abspath())


    def add_a_product(self, id, quantity=1, declination=None):
        self.manage_product(id, quantity, declination)


    def remove_a_product(self, id, quantity=-1, declination=None):
        self.manage_product(id, quantity, declination)


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

    #####################
    # Stock / quantity
    ######################
    def get_product_name(self, id):
        for p in self.products:
            if p['id'] == id:
                return p['name']
        return None


    def get_product_quantity_in_cart(self, product_name):
        for p in self.products:
            if p['name'] == product_name:
                return p['quantity']
        return 0

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
        if not cookie or cookie == 'deleted':
            return None
        cookie = Password.decode(cookie)
        name, option = cookie.split('|')
        return {'name': name, 'option': option}


    def set_shipping(self, shipping_name, shipping_option=''):
        value = Password.encode('%s|%s' % (shipping_name, shipping_option))
        cookie = self.context.set_cookie('shipping', value)

    ########################
    # Id zone
    ########################

    def _get_id_zone(self):
        cookie = self.context.get_cookie('id_zone')
        if not cookie or cookie == 'deleted':
            return None
        return Password.decode(cookie)


    def set_id_zone(self, id_zone):
        value = Password.encode(id_zone)
        cookie = self.context.set_cookie('id_zone', value)

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
        if not cookie or cookie == 'deleted':
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
        self._set_addresses(self.addresses['delivery_address'], id)


    # XXX To improve
    def get_total_price(self, shop, with_delivery=True, pretty=True):
        context = self.context
        total_price_with_tax = decimal(0)
        total_price_without_tax = decimal(0)
        total_weight = decimal(0)
        for cart_elt in self.products:
            product = context.root.get_resource(cart_elt['name'])
            quantity = cart_elt['quantity']
            declination = cart_elt['declination']
            unit_price_with_tax = product.get_price_with_tax(declination)
            unit_price_without_tax = product.get_price_without_tax(declination)
            total_price_with_tax += unit_price_with_tax * quantity
            total_price_without_tax += unit_price_without_tax * quantity
            total_weight += product.get_weight(declination) * quantity
        # XXX GEt Shipping price (Hardcoded, fix it)
        if with_delivery is True:
            shipping_price = self.get_shipping_ns(shop, context)['price']
            total_price_with_tax += shipping_price
            total_price_without_tax += shipping_price
        if pretty is True:
            return {'with_tax': format_price(total_price_with_tax),
                    'without_tax': format_price(total_price_without_tax)}
        return {'with_tax': total_price_with_tax,
                'without_tax': total_price_without_tax}


    def get_shipping_ns(self, shop, context):
        addresses = shop.get_resource('addresses').handler
        delivery_address = self.addresses['delivery_address']
        record = addresses.get_record(delivery_address)
        country = addresses.get_record_value(record, 'country')
        shippings = shop.get_resource('shippings')
        shipping_mode = self.shipping['name']
        # Guess shipping posibilities
        shippings_details = get_shippings_details(self, context)
        shippings = shop.get_resource('shippings')
        for s in shippings.get_namespace_shipping_ways(context,
                        country, shippings_details):
            if s['name'] == shipping_mode:
              return s


    ######################
    # Check validity
    ######################

    def is_valid(self):
        """
        To be valid a cart must contains:
          - shipping id, addresses id, products
        """
        return (self.shipping and self.shipping['name'] is not None and
                len(self.products) > 0 and
                self.addresses and
                self.addresses['delivery_address'] is not None)


    def clear(self):
        for key in ['products', 'addresses', 'shipping']:
            self.context.del_cookie(key)


    def clean(self):
        for key in ['addresses', 'shipping']:
            self.context.del_cookie(key)
