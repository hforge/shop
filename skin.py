# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Hervé Cauwelier <herve@itaapy.com>
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
from itools.core import get_abspath

# Import from ikaaro
from ikaaro.skins import Skin, register_skin

# Import from shop
from shop_utils_views import Cart_Viewbox


class BackofficeSkin(Skin):

    base_styles = ['/ui/common/style.css']

    def get_styles(self, context):
        styles = Skin.get_styles(self, context)
        styles.extend(self.base_styles)
        return styles


class ShopSkin(Skin):

    class_skin = 'ui/backoffice'
    base_styles = ['/ui/bo.css',
                   '/ui/shop/perfect_sale_style.css',
                   '/ui/shop/style.css']

    base_scripts = []

    def get_styles(self, context):
        styles = Skin.get_styles(self, context)
        styles.extend(self.base_styles)
        return styles


    def get_scripts(self, context):
        scripts = Skin.get_scripts(self, context)
        scripts.extend(self.base_scripts)
        return scripts


    def build_namespace(self, context):
        namespace = Skin.build_namespace(self, context)
        # Search
        namespace['product_search_text'] = context.get_query_value(
                                                'product_search_text')
        # Cart
        namespace['cart_preview'] = Cart_Viewbox().GET(context.resource,
                                                       context)
        return namespace


###########################################################################
# Register
###########################################################################
path = get_abspath('ui/shop/')
register_skin('shop', ShopSkin(path))

path = get_abspath('ui/backoffice/')
register_skin('backoffice', BackofficeSkin(path))

path = get_abspath('ui/modules/')
register_skin('modules', BackofficeSkin(path))
