# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
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
from itools.web import get_context
from itools.xapian import AndQuery, PhraseQuery
from itools.xml import xml_to_text

# Import from ikaaro
from ikaaro.forms import XHTMLBody, TextWidget, ImageSelectorWidget, RTEWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.registry import get_register_fields
from ikaaro.utils import get_base_path_query

# Import from itws
from itws.views import AutomaticEditView

# Import from shop
from categories_views import Category_View, Category_BackofficeView
from categories_views import Category_Comparator
from datatypes import ImagePathDataType
from folder import ShopFolder
from utils import get_shop
from products import Product
from products.product_views import Product_NewProduct, Products_View


class Category(ShopFolder):

    class_id = 'category'
    class_title = MSG(u'Category')

    # Edit configuration
    edit_show_meta = True
    edit_schema = {'data': XHTMLBody(multilingual=True),
                   'breadcrumb_title': Unicode(multilingual=True),
                   'image_category': ImagePathDataType(multilingual=True)}
    edit_widgets = [
        TextWidget('breadcrumb_title', title=MSG(u'Breadcrumb title')),
        ImageSelectorWidget('image_category',  title=MSG(u'Category image')),
        RTEWidget('data', title=MSG(u"Description"))]


    # Views
    view = Category_View()
    browse_content = Products_View()
    view_categories = Category_BackofficeView()
    edit = AutomaticEditView()
    new_product = Product_NewProduct()
    comparator = Category_Comparator()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           data=XHTMLBody(multilingual=True),
                           breadcrumb_title=Unicode(multilingual=True),
                           image_category=ImagePathDataType(multilingual=True))


    def _get_catalog_values(self):
        # Get the languages
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        default_language = languages[0]
        # Titles
        m_title = {}
        m_breadcrumb_title = {}
        for language in languages:
            value = self.get_property('title', language=language)
            if value:
                m_title[language] = value
            value = self.get_property('breadcrumb_title', language=language)
            if value:
                m_breadcrumb_title[language] = value
        # Data
        data = self.get_property('data')
        if data is not None:
            data = xml_to_text(data)
        return merge_dicts(ShopFolder._get_catalog_values(self),
                           data=data,
                           # XXX Hack to be on sitemap
                           workflow_state='public',
                           m_title=m_title,
                           m_breadcrumb_title=m_breadcrumb_title)


    def get_document_types(self):
        return [Product, Category]


    def get_nb_products(self, only_public=False):
        root = self.get_root()
        site_root = self.get_site_root()
        shop = get_shop(self)
        abspath = self.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(
            base_path_query,
            PhraseQuery('format', shop.product_class.class_id))
        if only_public is True:
            query.atoms.append(PhraseQuery('workflow_state', 'public'))
        return len(root.search(query))


    def get_nb_categories(self):
        root = self.get_root()
        site_root = self.get_site_root()
        shop = get_shop(self)
        abspath = self.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(
            base_path_query,
            PhraseQuery('format', shop.category_class.class_id))
        return len(root.search(query))


    #####################################
    ## XXX Hack to change class_views
    ## To report in ikaaro
    #####################################
    def get_class_views(self):
        context = get_context()
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return ['browse_content', 'view_categories', 'edit']
        return ['view']


    def get_default_view_name(self):
        views = self.get_class_views()
        if not views:
            return None
        context = get_context()
        user = context.user
        ac = self.get_access_control()
        for view_name in views:
            view = getattr(self, view_name, None)
            if ac.is_access_allowed(user, self, view):
                return view_name
        return views[0]


    def get_views(self):
        user = get_context().user
        ac = self.get_access_control()
        for name in self.get_class_views():
            view_name = name.split('?')[0]
            view = self.get_view(view_name)
            if ac.is_access_allowed(user, self, view):
                yield name, view



register_resource_class(Category)

# Add m_title field if it does not already exist
if 'm_title' in get_register_fields() is False:
    register_field('m_title', Unicode(is_stored=True, is_indexed=True))
register_field('m_breadcrumb_title', Unicode(is_stored=True, is_indexed=True))
