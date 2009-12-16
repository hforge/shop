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
from ikaaro.registry import register_resource_class
from ikaaro.utils import get_base_path_query

# Import from shop
from categories_views import VirtualCategories_View, Category_Edit
from categories_views import VirtualCategory_Comparator, Categories_View
from categories_views import VirtualCategory_View, VirtualCategory_ComparatorView
from utils import get_shop, ShopFolder
from editable import Editable


class Category(Editable, ShopFolder):

    class_id = 'category'
    class_title = MSG(u'Category')
    class_views = ['view', 'new_resource?type=category', 'edit']

    # Views
    view = Categories_View()
    edit = Category_Edit()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           Editable.get_metadata_schema(),
                           breadcrumb_title=Unicode(multilingual=True),
                           image_category=PathDataType(multilingual=True))


    def _get_catalog_values(self):
        return merge_dicts(ShopFolder._get_catalog_values(self),
                           Editable._get_catalog_values(self))


    def get_unique_id(self):
        """Get the path to get from the categories container to this category.
        Used by products to store the categories they belong to.
        """
        return str(self.get_abspath()).split('categories/', 1)[1]


    def get_document_types(self):
        return [Category]


    def get_nb_products(self, only_public=False):
        root = self.get_root()
        site_root = self.get_site_root()
        shop = get_shop(self)
        abspath = site_root.get_canonical_path()
        base_path_query = get_base_path_query(str(abspath))
        query = AndQuery(
            base_path_query,
            PhraseQuery('format', shop.product_class.class_id),
            PhraseQuery('categories', self.get_unique_id()))
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



class Categories(ShopFolder):

    class_id = 'categories'
    class_title = MSG(u'Categories')
    class_views = ['view', 'new_resource?type=category']

    view = Categories_View()

    def get_document_types(self):
        return [Category]



class VirtualCategory(Category):
    """The Category wrapper. No need to register it: it's built dynamically.
    """

    class_id = 'VirtualCategory'
    class_title = MSG(u"Category")
    class_views = ['view', 'compare']

    # Wrap products inside categories?
    # (the alternative is to wrap products in their own folder)
    wrap_products = True

    # Views
    view = VirtualCategory_View()
    compare = VirtualCategory_ComparatorView()
    comparator = VirtualCategory_Comparator()

    # XXX Back-office views can't apply
    browse_content = None
    preview_content = None
    new_resource = None
    last_changes = None
    orphans = None


    def _get_resource(self, name):
        """Get the virtual category.
        Or the virtual product if we expose products into categories.
        """
        shop = get_shop(self)
        # Get the real category
        real_resource = self.get_real_resource()
        try:
            resource = real_resource.get_resource(name)
        except LookupError:
            resource = None
        else:
            virtual_cls = shop.virtual_category_class
        # Or maybe the name matches a product
        if resource is None and self.wrap_products:
            try:
                resource = shop.get_resource('products/%s' % name)
            except LookupError:
                resource = None
            else:
                virtual_cls = shop.product_class
        if resource is None:
            return None
        # Return a copy of the resource wrapped into our virtual class
        return virtual_cls(resource.metadata)


    def get_document_types(self):
        return []


    #####################################
    ## XXX Hack to change class_views
    ## To report in ikaaro
    #####################################
    def get_class_views(self):
        shop = get_shop(self)
        return shop.categories_class_views


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



class VirtualCategories(ShopFolder):
    """The Virtual Categories Folder allows to publish categories (and
    products) in a front-office without exposing the shop module which
    belongs to the back-office.
    They also allow nice search engine optimisation with an user-friendly
    URL such as:
    http://example.com/categories/mycategory/mysubcategory
    or with products:
    http://example.com/categories/mycategory/mysubcategory/myproduct

    Plug it in your website::

      VirtualCategories.make_resource(VirtualCategories, self, 'categories',
                                      title={'en': u"Categories",
                                             'fr': u"Catégories"})

    While making the website itself or in an update method.
    """

    class_id = 'VirtualCategories'
    class_title = MSG(u"Categories")
    class_views =  ['view']

    view = VirtualCategories_View()
    comparator = VirtualCategory_Comparator()

    # Views
    # XXX Back-office views can't apply
    browse_content = None
    preview_content = None
    new_resource = None
    last_changes = None
    orphans = None

    # XXX do NOT implement "_get_names"
    # The virtual categories must NOT be indexed as real resources


    def get_canonical_path(self):
        site_root = self.get_site_root()
        categories = site_root.get_resource('shop/categories')
        return categories.get_canonical_path()


    def _get_resource(self, name):
        shop = get_shop(self)
        category = shop.get_resource('categories/%s' % name, soft=True)
        if category is None:
            return None
        metadata = category.metadata
        # Build another instance with the same properties
        return shop.virtual_category_class(metadata)


    def search_resources(self, cls=None, format=None, state=None):
        # We implement search_resources to show virtual categories
        # XXX Show compatibility in 0.70
        real_category = self.get_real_resource()
        return real_category.search_resources(cls=Category)



    def get_document_types(self):
        return []



register_resource_class(Category)
register_resource_class(Categories)
register_resource_class(VirtualCategories)
