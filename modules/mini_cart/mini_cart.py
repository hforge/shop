# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.gettext import MSG
from itools.web import STLView

# Import from shop
from shop.cart import ProductCart
from shop.folder import ShopFolder
from shop.utils import get_shop, get_skin_template


class ShopModule_MiniCart_View(STLView):

    access = True

    def get_template(self, resource, context):
        return get_skin_template(context, '/modules/mini_cart.xml')


    def get_namespace(self, resource, context):
        cart = ProductCart(context)
        nb_products = cart.get_nb_products()
        shop = get_shop(context.resource)
        # Get total price
        total = cart.get_total_price(shop, with_delivery=False)
        if shop.show_ht_price(context):
            total = total['without_tax']
        else:
            total = total['with_tax']
        # Return namespace
        return {'nb_products': nb_products,
                'total': total,
                'txts_class': 'hidden' if nb_products < 2 else '',
                'txt_class': 'hidden' if nb_products > 1 else ''}



class ShopModule_MiniCart(ShopFolder):

    class_id = 'shop_module_mini_cart'
    class_title = MSG(u'Mini cart')
    class_views = ['view']
    class_description = MSG(u'Mini cart')

    def render(self, resource, context):
        return ShopModule_MiniCart_View().GET(self, context)
