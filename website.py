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
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.registry import register_resource_class, register_document_type
from ikaaro.website import WebSite

# Import from itws
from itws.sitemap import SiteMap, SiteMapView
from itws.ws_neutral import NeutralWS

# Import from shop
from categories import Category
from search import ShopSearch
from shop import Shop
from shop_views import Shop_Register, Shop_Login
from shop_utils_views import Cart_Viewbox
from utils_views import RedirectPermanent
from website_views import ShopWebSite_View, ShopWS_SiteMap, ShopWS_RSS


default_resources = {
    'shop': (Shop, {'title': {'en': u'Shop'}, 'state':'public'}),
    'categories': (Category, {'title': {'en': u"Categories"}}),
    'seach': (ShopSearch, {'title': {'en': u'Search'}}),
}


# XXX ??
class ShopXMLSiteMap(SiteMap):

    class_id = 'shop-sitemap'

    view = SiteMapView()



class ShopWebSite(NeutralWS):

    class_id = 'shop-website'
    class_title = MSG(u'Shop website')
    class_views = ['view', 'edit', 'edit_rss',
                   'browse_content', 'control_panel', 'last_changes']
    class_version = '20100227'
    class_skin = '/ui/default_skin'

    __fixed_handlers__ = WebSite.__fixed_handlers__ + ['categories', 'shop']

    # View
    view = ShopWebSite_View()
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
    sitemap_class = ShopXMLSiteMap
    templates = {}
    cart_preview_class = Cart_Viewbox
    backoffice_rss_news_uri = None

    # Skin configuration
    show_sidebar_on_product = True
    show_sidebar_on_category = True
    show_sidebar_on_homepage = True



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


    def get_document_types(self):
        return []


    def get_skin(self, context):
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return self.get_resource('/ui/backoffice/')
        # Fron-Office
        return self.get_resource(self.class_skin)

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



register_resource_class(ShopWebSite)
register_document_type(ShopWebSite, WebSite.class_id)
register_resource_class(ShopXMLSiteMap)
