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
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.registry import register_resource_class, register_document_type
from ikaaro.website import WebSite

# Import from itws
from itws.ws_neutral import NeutralWS

# Import from shop
from categories import Category
from datatypes import SkinsEnumerate
from manufacturers import Manufacturers
from search import ShopSearch
from shop import Shop
from shop_views import Shop_Register, Shop_Login
from shop_utils_views import Cart_Viewbox
from utils_views import RedirectPermanent
from website_views import ShopWebSite_View, ShopWS_SiteMap, ShopWS_RSS
from website_views import ShopWebSite_Configure


default_resources = {
    'categories': (Category, {'title': {'en': u"Categories"}}),
    'manufacturers': (Manufacturers, {'title': {'en': u"Manufacturers"}}),
    'search': (ShopSearch, {'title': {'en': u'Search'}}),
    'shop': (Shop, {'title': {'en': u'Shop'}, 'state':'public'}),
}


class ShopWebSite(NeutralWS):

    class_id = 'shop-website'
    class_title = MSG(u'Shop website')
    class_version = '20100712'
    class_skin = '/ui/default_skin/'

    __fixed_handlers__ = NeutralWS.__fixed_handlers__ + ['categories', 'shop']

    edit_schema = {}
    edit_widgets = []

    # View
    view = ShopWebSite_View()
    configure = ShopWebSite_Configure()
    sitemap = ShopWS_SiteMap()
    product_search = RedirectPermanent(specific_document='search')

    # Login views
    register = Shop_Register()
    login = Shop_Login()
    unauthorized = Shop_Login()

    # Compatibility
    rss = last_news_rss = ShopWS_RSS()


    # Shop configuration
    shop_class = Shop
    templates = {}
    cart_preview_class = Cart_Viewbox
    backoffice_rss_news_uri = None


    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        root = get_context().resource
        NeutralWS._make_resource(cls, folder, name, **kw)
        website = root.get_resource(name)
        # Configuration des langues
        metadata = website.metadata
        metadata.set_property('website_languages', ('fr', 'en'))

        # Site public
        metadata.set_property('website_is_open', True)

        # Configuration des sites
        metadata.set_property('vhosts', ('shop', 'shop.com'))

        # Ressources par défaut
        for name2, (cls, kw) in default_resources.items():
            cls._make_resource(cls, folder, '%s/%s' % (name, name2),
                               language='en', **kw)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(
                  NeutralWS.get_metadata_schema(),
                  class_skin=SkinsEnumerate)


    def get_document_types(self):
        return []


    def get_class_skin(self, context):
        class_skin = self.get_property('class_skin')
        if not class_skin:
            return self.class_skin
        return class_skin


    def get_skin(self, context):
        if context.get_query_value('is_admin_popup', type=Boolean) is True:
            return self.get_resource('/ui/admin-popup/')
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return self.get_resource('/ui/backoffice/')
        # Fron-Office
        return self.get_resource(self.get_class_skin(context))

    #############################
    # ACL
    #############################
    def is_owner_or_admin(self, user, resource):
        if not user:
            return False
        # Admins are all powerfull
        if self.is_admin(user, resource):
            return True
        owner = resource.get_property('owner')
        return owner == user.name


    #############################
    # Update
    #############################
    def update_20100227(self):
        self.move_resource('categories', 'categories_old')
        self.move_resource('shop/categories', 'categories')


    def update_20100228(self):
        resource = self.get_resource('categories')
        metadata = resource.metadata
        metadata.version = Category.class_version
        metadata.format = Category.class_id
        metadata.set_changed()


    def update_20100601(self):
        from sidebar import CategorySidebar
        from sidebar import ProductSidebar
        cls = CategorySidebar
        cls.make_resource(cls, self, 'category-sidebar')
        cls = ProductSidebar
        cls.make_resource(cls, self, 'product-sidebar')


    def update_20100712(self):
        from sidebar import ShopSidebar
        cls = ShopSidebar
        shop = self.get_resource('shop')
        cls.make_resource(cls, shop, 'shop-sidebar')


    def update_20100803(self):
        resource = self.get_resource('sitemap.xml')
        metadata = resource.metadata
        metadata.format = 'sitemap'
        metadata.set_changed()


register_resource_class(ShopWebSite)
register_document_type(ShopWebSite, WebSite.class_id)
