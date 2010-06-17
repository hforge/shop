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
from itools.core import merge_dicts
from itools.datatypes import Boolean, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import TextWidget, BooleanRadio
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import Box, register_box
from itws.repository_views import Box_View

# Import from shop
from shop.cart import ProductCart



class CartBox_View(Box_View):

    template = '/ui/vertical_depot/cart_box.xml.fr'

    def get_namespace(self, resource, context):
        show_if_empty = resource.get_property('show_if_empty')
        cart = ProductCart(context)
        if (self.is_admin(resource, context) is False and
            cart.get_nb_products() == 0 and
            show_if_empty is False):
            self.set_view_is_empty(True)

        default_order_title = MSG(u'Commander')
        return merge_dicts(
            cart.get_namespace(resource),
            order_title=resource.get_property('order_title') or default_order_title,
            title=resource.get_title())



class CartBox(Box):

    class_id = 'vertical-item-cart-box'
    class_title = MSG(u'Boîte panier')
    view = CartBox_View()


    edit_schema = {'order_title': Unicode(multilingual=True),
                   'show_if_empty': Boolean}

    edit_widgets = [TextWidget('order_title', title=MSG(u'Order title')),
                    BooleanRadio('show_if_empty',
                                 title=MSG(u'Show cart if empty ?'))]


register_resource_class(CartBox)
register_box(CartBox, allow_instanciation=False)
