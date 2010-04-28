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
from itools.gettext import MSG, get_domain
from itools.i18n import get_language_name

# Import from ikaaro
from ikaaro.future.menu import get_menu_namespace
from ikaaro.skins import Skin, register_skin
from ikaaro.website import WebSite

# Import from itws
from itws.common import LocationTemplateWithoutTab, CommonLanguagesTemplate
from itws.utils import is_empty
from itws.ws_neutral import NeutralSkin

# Import from shop
from products import Product
from utils import get_shop


class ShopLocationTemplate(LocationTemplateWithoutTab):

    excluded = ['/categories/']
    skip_breadcrumb_in_homepage = True
    bc_separator = '>'
    homepage_name = 'index'
    tabs_hidden_roles = ('guests',)



class ShopLanguagesTemplate(CommonLanguagesTemplate):

    def get_namespace(self):
        context = self.context
        site_root = context.resource.get_site_root()
        shop = site_root.get_resource('shop')
        here = context.resource

        if isinstance(here, shop.product_class) is False:
            return CommonLanguagesTemplate.get_namespace(self)

        # Special case for the product of the shop
        # If the user can edit the resource, we display all the languages
        here = context.resource
        ac = here.get_access_control()
        allowed = ac.is_allowed_to_edit(context.user, here)
        if allowed:
            return CommonLanguagesTemplate.get_namespace(self)

        # Website languages
        ws_languages = site_root.get_property('website_languages')
        # Select language
        accept = context.accept_language
        current_language = accept.select_language(ws_languages)
        # Sort the available languages
        ws_languages = list(ws_languages)
        ws_languages.sort()

        available_langs = []
        for language in ws_languages:
            # data (html)
            # XXX It should be usefull to index the available languages for
            # the html and the description
            events = here.get_xhtml_data(language=language)
            title = here.get_property('title', language=language)
            if is_empty(events) is False and len(title.strip()):
                available_langs.append(language)

        languages = []
        gettext = get_domain('itools').gettext
        for language in available_langs:
            href = context.uri.replace(language=language)
            selected = (language == current_language)
            css_class = 'selected' if selected else None
            value = get_language_name(language)
            languages.append({
                'name': language,
                'value': gettext(value, language),
                'href': href,
                'selected': selected,
                'class': css_class})

        return {'languages': languages}




class BackofficeSkin(Skin):

    base_styles = ['/ui/common/style.css']

    def get_styles(self, context):
        styles = Skin.get_styles(self, context)
        styles.extend(self.base_styles)
        return styles




class ShopSkin(NeutralSkin):

    base_styles = ['/ui/shop/perfect_sale_style.css',
                   '/ui/shop/style.css']

    base_scripts = []

    menu_level = 1
    location_template = ShopLocationTemplate
    languages_template = ShopLanguagesTemplate


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
        styles = NeutralSkin.get_styles(self, context)
        styles.append('/ui/shop/style.css')
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
        # Show sidebar
        if isinstance(here, site_root.shop_class):
            namespace['sidebar_view'] = None
        elif (isinstance(here, shop.product_class) and
            site_root.show_sidebar_on_product is False):
            namespace['sidebar_view'] = None
        elif (isinstance(here, shop.category_class) and
              site_root.show_sidebar_on_category is False):
            namespace['sidebar_view'] = None
        elif (isinstance(here, WebSite) and
            site_root.show_sidebar_on_homepage is False):
            namespace['sidebar_view'] = None
        return namespace



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
