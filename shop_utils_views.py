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

# Import from itools
from itools.gettext import MSG
from itools.stl import stl
from itools.web import STLView, STLForm

# Import from shop
from cart import ProductCart
from utils import format_price, get_shop



class Shop_Progress(STLView):
    """ Graphic progress bar that inform user
    of payment progression (6 Steps)
    """
    access = True
    title = None
    template = '/ui/shop/shop_progress.xml'

    def get_namespace(self, resource, context):
        ns = {'title': self.title,
              'progress': {}}
        for i in range(0, 7):
            css = 'active' if self.index == i else None
            ns['progress'][str(i)] = css
        return ns


class Cart_View(STLView):

    access = True
    template = '/ui/shop/cart_view.xml'

    def get_namespace(self, resource, context):
        namespace = {'products': [],
                     'see_actions': self.see_actions}
        abspath = resource.get_abspath()
        # Get cart
        cart = ProductCart(context)
        # Get products
        products = resource.get_resource('products')
        # Get products informations
        total_weight = decimal(0)
        total = {'with_tax': decimal(0),
                 'without_tax': decimal(0)}
        for product_cart in cart.products:
            # Get product
            product = products.get_resource(product_cart['name'], soft=True)
            # Check product is buyable
            if not product or not product.is_buyable():
                continue
            quantity = product_cart['quantity']
            declination = product_cart['declination']
            # Weight
            total_weight +=  product.get_weight(declination)
            # Prices
            declination = product_cart['declination']
            unit_price_with_tax = product.get_price_with_tax(declination)
            unit_price_without_tax = product.get_price_without_tax(declination)
            total_price_with_tax = unit_price_with_tax * quantity
            total_price_without_tax = unit_price_without_tax * quantity
            price = {
              'unit': {'with_tax': format_price(unit_price_with_tax),
                       'without_tax': format_price(unit_price_without_tax)},
              'total': {'with_tax': format_price(total_price_with_tax),
                        'without_tax': format_price(total_price_without_tax)}}
            total['without_tax'] += total_price_without_tax
            total['with_tax'] += total_price_with_tax
            # All
            declination = product_cart['declination']
            if declination:
                declination = product.get_declination_namespace(declination)
            can_add_quantity = product.is_in_stock_or_ignore_stock(quantity+1)
            namespace['products'].append(
              {'id': product_cart['id'],
               'name': product.name,
               'img': product.get_cover_namespace(context),
               'title': product.get_title(),
               'href': abspath.get_pathto(product.get_virtual_path()),
               'can_add_quantity': can_add_quantity,
               'quantity': quantity,
               'declination': declination,
               'price': price})
        namespace['total'] = total
        # Get shippings
        namespace['ship'] = None
        if cart.shipping:
            shipping_mode = cart.shipping['name']
            shippings = resource.get_resource('shippings')
            addresses = resource.get_resource('addresses').handler
            delivery_address = cart.addresses['delivery_address']
            record = addresses.get_record(delivery_address)
            country = addresses.get_record_value(record, 'country')
            namespace['ship'] = shippings.get_namespace_shipping_way(context,
                                    shipping_mode, country, total_weight)
            namespace['total']['with_tax'] += namespace['ship']['price']
            namespace['total']['without_tax'] += namespace['ship']['price']
        # Format total prices
        for key in ['with_tax', 'without_tax']:
            namespace['total'][key] = format_price(namespace['total'][key])
        return namespace


class Cart_Viewbox(STLView):

    access = True
    template = '/ui/shop/cart_viewbox.xml'

    def GET(self, resource, context):
        cart = ProductCart(context)
        if cart.get_nb_products() <= 0:
            return
        return STLView.GET(self, resource, context)


    def get_namespace(self, resource, context):
        cart = ProductCart(context)
        return cart.get_namespace(resource)



class RealRessource_Form(STLForm):

    def get_real_resource(self, resource, context):
        raise NotImplementedError


    def GET(self, resource, context):
        real_resource = self.get_real_resource(resource, context)
        return STLForm.GET(self, real_resource, context)


    def POST(self, resource, context):
        real_resource = self.get_real_resource(resource, context)
        return STLForm.POST(self, real_resource, context)




class Shop_PluginWay_Form(STLForm):

    def GET(self, order, way, record, context):
        # Get the template
        template = self.get_template(order, context)
        # Get the namespace
        namespace = self.get_namespace(order, way, record, context)
        # Ok
        return stl(template, namespace)
