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
from itools.datatypes import PathDataType
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from shop
from categories_views import VirtualCategories_View, Category_Edit
from categories_views import VirtualCategory_BoxSubCategories
from categories_views import VirtualCategory_Comparator, Categories_View
from categories_views import VirtualCategory_View, VirtualCategory_ComparatorView
from products import Product
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


    def change_link(self, old_path, new_path):
        # Use the canonical path instead of the abspath
        # Warning multilingual property
        site_root = self.get_site_root()
        base = self.get_canonical_path()

        available_languages = site_root.get_property('website_languages')
        for lang in available_languages:
            path = self.get_property('image_category', language=lang)
            if not path:
                continue
            current_path = base.resolve2(path)
            if str(current_path) == old_path:
                # Hit the old name
                updated_path = base.get_pathto(Path(new_path))
                self.set_property('image_category', str(updated_path),
                                  language=lang)

        get_context().server.change_resource(self)





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
    view2 = VirtualCategory_BoxSubCategories() # XXX to remove
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


    def get_document_types(self):
        return []



register_resource_class(Category)
register_resource_class(Categories)
register_resource_class(VirtualCategories)
