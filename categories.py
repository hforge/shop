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

# Import from the Standard Library
from copy import deepcopy

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import PathDataType, Unicode
from itools.gettext import MSG
from itools.uri import Path, get_reference
from itools.web import get_context
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.registry import register_resource_class, register_field
from ikaaro.registry import get_register_fields
from ikaaro.utils import get_base_path_query

# Import from shop
from categories_views import Category_View, Category_Edit
from categories_views import Category_ComparatorView, Category_Comparator
from categories_views import Category_BackofficeView
from utils import get_shop, ShopFolder
from editable import Editable
from products import Product
from products.product_views import Product_NewProduct


class Category(Editable, ShopFolder):

    class_id = 'category'
    class_title = MSG(u'Category')

    # Views
    view = Category_View()
    view_backoffice = Category_BackofficeView()
    edit = Category_Edit()
    new_product = Product_NewProduct()
    compare = Category_ComparatorView()
    comparator = Category_Comparator()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           Editable.get_metadata_schema(),
                           breadcrumb_title=Unicode(multilingual=True),
                           image_category=PathDataType(multilingual=True))


    def _get_catalog_values(self):
        # Get the languages
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        default_language = languages[0]
        # Titles
        m_title = {}
        for language in languages:
            value = self.get_property('title', language=language)
            if value:
                m_title[language] = value

        return merge_dicts(ShopFolder._get_catalog_values(self),
                           Editable._get_catalog_values(self),
                           m_title=m_title)


    def get_document_types(self):
        return [Category, Product]


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
        return root.search(query).get_n_documents()



    def get_links(self):
        # Use the canonical path instead of the abspath
        # Warning multilingual property
        site_root = self.get_site_root()
        base = self.get_canonical_path()
        links = []
        available_languages = site_root.get_property('website_languages')
        for lang in available_languages:
            path = self.get_property('image_category', language=lang)
            if path:
                links.append(str(base.resolve2(path)))
        return links



    def update_links(self,  source, target):
        # Use the canonical path instead of the abspath
        # Warning multilingual property
        site_root = self.get_site_root()
        base = self.get_canonical_path()
        base = str(base)
        resources_new2old = get_context().database.resources_new2old
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        available_languages = site_root.get_property('website_languages')
        for lang in available_languages:
            path = self.get_property('image_category', language=lang)
            if not path:
                continue
            path = old_base.resolve2(path)
            if str(path) == source:
                # Hit the old name
                new_path = new_base.get_pathto(target)
                self.set_property('image_category', str(new_path),
                                  language=lang)

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        site_root = self.get_site_root()
        available_languages = site_root.get_property('website_languages')

        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        for lang in available_languages:
            path = self.get_property('image_category', language=lang)
            if not path:
                continue
            ref = get_reference(path)
            if ref.scheme:
                continue
            path = ref.path
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Check if the target path has not been moved
            new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)
            # Build the new reference with the right path
            # Absolute path allow to call get_pathto with the target
            new_ref = deepcopy(ref)
            new_ref.path = target.get_pathto(new_abs_path)
            self.set_property('image_category', str(new_ref), language=lang)

    #####################################
    ## XXX Hack to change class_views
    ## To report in ikaaro
    #####################################
    def get_class_views(self):
        context = get_context()
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return ['view_backoffice', 'edit']
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
    # multilingual title with language negociation
    register_field('m_title', Unicode(is_stored=True, is_indexed=True))
