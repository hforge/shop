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
from ikaaro.wiki import WikiFolder

# Import from itws
from itws.tracker import ITWSTracker
from itws.ws_neutral import NeutralWS

# Import from shop
from categories import Category
from datatypes import SkinsEnumerate
from manufacturers import Manufacturers
from search import ShopSearch
from shop import Shop
from shop_views import Shop_Register, Shop_Login
from shop_utils_views import Cart_Viewbox
from sidebar import CategorySidebar, ProductSidebar
from utils_views import RedirectPermanent
from website_views import ShopWebSite_View, ShopWS_SiteMap, ShopWS_RSS
from website_views import ShopWebSite_Edit


default_resources = {
    'categories': (Category, {'title': {'en': u"Categories"}}),
    'category-sidebar': (CategorySidebar, {'title': {'en': u'Category sidebar'}}),
    'manufacturers': (Manufacturers, {'title': {'en': u"Manufacturers"}}),
    'product-sidebar': (ProductSidebar, {'title': {'en': u'Product sidebar'}}),
    'search': (ShopSearch, {'title': {'en': u'Search'}}),
    'shop': (Shop, {'title': {'en': u'Shop'}, 'state':'public'}),
    'tracker': (ITWSTracker, {}),
    'wiki': (WikiFolder, {}),
}



class ShopWebSite(NeutralWS):

    class_id = 'shop-website'
    class_title = MSG(u'Shop website')
    class_version = '20100712'
    class_skin = '/ui/default_skin/'

    __fixed_handlers__ = NeutralWS.__fixed_handlers__ + ['categories', 'shop']


    # View
    view = ShopWebSite_View()
    edit = ShopWebSite_Edit()
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
    cart_preview_class = Cart_Viewbox
    backoffice_rss_news_uri = None
    backoffice_announce_uri = None


    @staticmethod
    def _make_resource(cls, folder, name, **kw):
        root = get_context().resource
        NeutralWS._make_resource(cls, folder, name, **kw)
        website = root.get_resource(name)
        # Languages (En and Fr)
        metadata = website.metadata
        metadata.set_property('website_languages', ('en', 'fr', ))

        # Website is open
        metadata.set_property('website_is_open', True)

        # Default resources
        for name2, (cls, kw) in default_resources.items():
            cls._make_resource(cls, folder, '%s/%s' % (name, name2), **kw)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(
                  NeutralWS.get_metadata_schema(),
                  hide_website_title_on_meta_title=Boolean,
                  class_skin=SkinsEnumerate,
                  class_skin_administrators=SkinsEnumerate)


    def get_class_skin(self, context):
        class_skin = self.get_property('class_skin')
        if not class_skin:
            return self.class_skin
        ac = self.get_access_control()
        if ac.is_admin(context.user, self):
            return self.get_property('class_skin_administrators')
        return class_skin


    def get_skin(self, context):
        if context.get_query_value('is_admin_popup', type=Boolean) is True:
            return self.get_resource('/ui/admin-popup/')
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return self.get_resource('/ui/backoffice/')
        # Front-Office
        class_skin = self.get_class_skin(context)
        skin = self.get_resource(class_skin, soft=True)
        if skin is None:
            skin = self.get_resource('/ui/default_skin/')
        return skin


    def is_allowed_to_view_for_authenticated(self, user, resource):
        if (resource.has_property('must_be_authentificated') and
            resource.get_property('must_be_authentificated')):
            return self.is_authenticated(user, resource)
        return self.is_allowed_to_view(user, resource)


register_resource_class(ShopWebSite)
register_document_type(ShopWebSite, WebSite.class_id)


# XXX Add a hack to change login page
from ikaaro.resource_ import DBResource
DBResource.login = Shop_Login()
