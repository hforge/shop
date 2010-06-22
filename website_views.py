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
from itools.core import merge_dicts
from itools.datatypes import Unicode
from itools.gettext import MSG
from itools.web import STLView
from itools.xapian import PhraseQuery, AndQuery, OrQuery

# Import from ikaaro
from ikaaro.utils import get_base_path_query

# Import from itws
from itws.ws_neutral_views import NeutralWS_RSS, NeutralWS_View

# Import from shop
from categories import Category
from products import Product
from utils import get_shop


class ShopWebSite_View(NeutralWS_View):

    title = MSG(u'View')
    access = 'is_allowed_to_view'

    subviews = merge_dicts(NeutralWS_View.subviews,
                           vertical_items_view=None)


    def GET(self, resource, context):
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return context.uri.resolve('/shop/;administration')
        return NeutralWS_View.GET(self, resource, context)



class ShopWS_RSS(NeutralWS_RSS):

    access = True

    def get_base_query(self, resource, context):
        query = NeutralWS_RSS.get_base_query(self, resource, context)
        # Add products
        site_root = resource.get_site_root()
        shop = site_root.get_resource('shop')
        abspath = site_root.get_canonical_path()
        product_query = [PhraseQuery('format', shop.product_class.class_id),
                         PhraseQuery('workflow_state', 'public'),
                         get_base_path_query(str(abspath))]
        return [ OrQuery(AndQuery(*query), AndQuery(*product_query)) ]


    def get_item_value(self, resource, context, item, column, site_root):
        brain, item_resource = item
        if isinstance(item_resource, Product) is False:
            return NeutralWS_RSS.get_item_value(self, resource, context,
                                                item, column, site_root)
        if column == 'description':
            value = item_resource.get_property('data')
            value = Unicode.decode(value)
            # Add category
            category = item_resource.parent
            value = u'%s <br/><br/>Catégorie %s' % (value, category.get_title())
            return value
        return NeutralWS_RSS.get_item_value(self, resource, context,
                                            item, column, site_root)



class ShopWS_SiteMap(STLView):

    access = 'is_allowed_to_view'
    template = '/ui/shop/sitemap.xml'


    def build_tree(self, resource, context, level):
        items = []
        if not level:
            return None
        root = context.root
        shop = get_shop(resource)
        product_format = shop.product_class.class_id
        product_query = AndQuery(PhraseQuery('format', product_format),
                                 PhraseQuery('workflow_state', 'public'))

        for category in resource.search_resources(cls=Category):
            href = context.get_link(category)
            sub_tree = self.build_tree(category, context, level - 1)
            img = None
            img_path = category.get_property('image_category')
            if img_path.get_name():
                try:
                    img = category.get_resource(img_path)
                    img = context.get_link(img)
                except LookupError:
                    pass
            nb_products = category.get_nb_products(only_public=True)
            category_tree = {'title': category.get_title(),
                             'href': href,
                             'img_src': img,
                             'sub_tree': sub_tree,
                             'empty': nb_products==0}
            items.append(category_tree)
        return items


    def get_namespace(self, resource, context):
        namespace = {}
        categories = resource.get_resource('categories')
        # Get sub categories
        site_root = resource.get_site_root()
        namespace['categories'] = self.build_tree(categories, context, 2)
        return namespace
