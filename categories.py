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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from shop
from products import Product
from categories_views import VirtualCategory_View, VirtualCategory_ComparatorView
from categories_views import VirtualCategory_BoxSubCategories
from categories_views import VirtualCategory_Comparator, Categories_View


class Category(Folder):

    class_id = 'category'
    class_title = MSG(u'Category')
    class_views = ['browse_content', 'new_resource?type=category', 'edit']


    def get_unique_id(self):
        """Get the path to get from the categories container to this category.
        Used by products to store the categories they belong to.
        """
        return str(self.get_abspath()).split('categories/', 1)[1]


    def get_document_types(self):
        return [Category]



class Categories(Folder):

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

    # Class to wrap subcategories into
    # Default is ourself
    virtual_category_class = None
    # Class to wrap products into
    # Default is the base shop Product
    virtual_product_class = Product

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
        # Get the real category
        real_resource = self.get_real_resource()
        try:
            resource = real_resource.get_resource(name)
        except LookupError:
            resource = None
        else:
            virtual_cls = self.virtual_category_class or self.__class__
        # Or maybe the name matches a product
        if resource is None and self.wrap_products:
            site_root = self.get_site_root()
            try:
                resource = site_root.get_resource('shop/products/%s' % name)
            except LookupError:
                resource = None
            else:
                virtual_cls = self.virtual_product_class
        if resource is None:
            return None
        # Return a copy of the resource wrapped into our virtual class
        return virtual_cls(resource.metadata)



class VirtualCategories(Folder):
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

    # Class to wrap categories into
    virtual_category_class = VirtualCategory

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
        site_root = self.get_site_root()
        category = site_root.get_resource('shop/categories/%s' % name,
                                          soft=True)
        if category is None:
            return None
        metadata = category.metadata
        # Build another instance with the same properties
        return self.virtual_category_class(metadata)




register_resource_class(Category)
register_resource_class(Categories)
register_resource_class(VirtualCategories)
