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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.future.menu import get_menu_namespace
from ikaaro.skins import Skin, register_skin
from ikaaro.website import WebSite

# Import from itws
from itws.common import LocationTemplateWithoutTab
from itws.ws_neutral import NeutralSkin

# Import from shop
from modules import ModuleLoader
from products import Product
from utils import get_shop


class ShopLocationTemplate(LocationTemplateWithoutTab):

    excluded = []
    skip_breadcrumb_in_homepage = True
    bc_separator = '>'
    homepage_name = 'index'
    tabs_hidden_roles = ('guests',)



class BackofficeSkin(Skin):

    base_styles = ['/ui/common/style.css']

    def get_styles(self, context):
        styles = Skin.get_styles(self, context)
        styles.extend(self.base_styles)
        styles.append('/ui/common/js/jquery.multiselect2side/css/jquery.multiselect2side.css')
        return styles


    def get_scripts(self, context):
        scripts = Skin.get_scripts(self, context)
        scripts.append('/ui/common/js/javascript.js')
        scripts.append('/ui/common/js/jquery.multiselect2side/js/jquery.multiselect2side.js')
        return scripts


class ShopSkinDynamicProperty(dict):

    resource = None
    context = None

    def __getitem__(self, key):
        if key == 'current_category':
            return self.resource.get_lazy_current_category(self.context)



class ShopSkin(NeutralSkin):

    base_styles = ['/ui/shop/perfect_sale_style.css',
                   '/ui/shop/style.css']

    base_scripts = []

    menu_level = 1
    location_template = ShopLocationTemplate


    def get_template_title(self, context):
        here = context.resource
        # In the website
        site_root = here.get_site_root()
        if site_root is here:
            return site_root.get_title()
        # Somewhere else
        message = MSG(u"{here_title} > {root_title}")
        return message.gettext(root_title=site_root.get_title(),
                               here_title=here.get_title())


    def get_styles(self, context):
        styles = ['/ui/shop/style.css']
        styles.extend(NeutralSkin.get_styles(self, context))
        styles.remove('/ui/common/menu.css')
        return styles


    def build_namespace(self, context):
        here = context.resource
        shop = get_shop(here)
        site_root = context.resource.get_site_root()
        namespace = NeutralSkin.build_namespace(self, context)
        # Menu XXX Done in ikaaro nav
        namespace['menu'] = get_menu_namespace(context, self.menu_level, src='menu')
        # Search
        namespace['product_search_text'] = context.get_query_value(
                                                'product_search_text')
        # XXX Page id css (see itws)
        class_id = getattr(here, 'class_id', None)
        if class_id:
            view_name = context.view_name or here.get_default_view_name()
            page_css_id = 'page-%s-%s' % (class_id, view_name)
            page_css_id = page_css_id.replace('_', '-')
            namespace['page_css_id'] = page_css_id.lower()
        else:
            namespace['page_css_id'] = None

        # Cart preview
        cart_preview = site_root.cart_preview_class().GET(shop, context)
        namespace['cart_preview'] = cart_preview
        # Page title
        namespace['page_title'] = context.resource.get_title()
        # Current view type
        namespace['is_on_view_product'] = isinstance(context.resource, Product)
        # Dynamic property
        dynamic_property = ShopSkinDynamicProperty()
        dynamic_property.context = context
        dynamic_property.resource = self
        namespace['dynamic_property'] = dynamic_property
        # Modules
        shop_module = ModuleLoader()
        shop_module.context = context
        shop_module.here = context.resource
        namespace['module'] = shop_module
        return namespace


    def get_sidebar_resource(self, context):
        # Show sidebar
        here = context.resource
        shop = get_shop(here)
        site_root = here.get_site_root()
        if isinstance(here, site_root.shop_class):
            return None
        elif isinstance(here, shop.product_class):
            if site_root.show_sidebar_on_product is False:
                return None
            return site_root.get_resource('product-sidebar')
        elif isinstance(here, shop.category_class):
            if site_root.show_sidebar_on_category is False:
                return None
            return site_root.get_resource('category-sidebar')
        elif (isinstance(here, WebSite) and
            site_root.show_sidebar_on_homepage is False):
            return None
        return NeutralSkin.get_sidebar_resource(self, context)


    # Lazy (dynamic property)
    def get_lazy_current_category(self, context):
        here = context.resource
        shop = get_shop(here)
        here = context.resource
        if isinstance(here, shop.category_class):
            return here.get_title()
        elif isinstance(here, shop.product_class):
            return here.parent.get_title()
        return None


###########################################################################
# Register
###########################################################################
path = get_abspath('ui/shop/')
register_skin('shop', ShopSkin(path))

path = get_abspath('ui/backoffice/')
register_skin('backoffice', BackofficeSkin(path))

path = get_abspath('ui/modules/')
register_skin('modules', Skin(path))

path = get_abspath('ui/default_skin/')
register_skin('default_skin', ShopSkin(path))
