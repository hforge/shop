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
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent
from ikaaro.folder_views import Folder_NewResource, Folder_LastChanges
from ikaaro.folder_views import Folder_Orphans
from ikaaro.registry import register_resource_class

# Import from shop
from products import Product


class Categorie(Folder):

    class_id = 'categorie'
    class_title = MSG(u'Categorie')
    class_views = ['browse_content', 'new_resource?type=categorie', 'edit']

    def get_document_types(self):
        return [Categorie]



class Categories(Folder):

    class_id = 'categories'
    class_title = MSG(u'Categories')
    class_views = ['browse_content', 'new_resource?type=categorie']

    def get_document_types(self):
        return [Categorie]



class VirtualCategory(Categorie):
    """The Category wrapper. No need to register it: it's built dynamically.
    """

    class_id = 'VirtualCategory'
    class_title = MSG(u"Category")

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
    # XXX Back-office views can't apply
    browse_content = Folder_BrowseContent(access=False)
    preview_content = Folder_PreviewContent(access=False)
    new_resource = Folder_NewResource(access=False)
    last_changes = Folder_LastChanges(access=False)
    orphans = Folder_Orphans(access=False)


    def get_canonical_path_and_resource(self, name):
        """Get the real resource and its abspath, but wrapped into our virtual
        classes.
        """
        category_class = self.virtual_category_class or self.__class__
        # Try if the name matches a category then a subcategory
        # TODO better heuristic to find subcategories
        search_paths = [('shop/categories/%s' % name, category_class),
                        ('shop/categories/%s/%s' % (self.name, name),
                         category_class)]
        # Try at demand if the name matches a product
        if self.wrap_products:
            search_paths.append(('shop/products/%s' % name,
                                 self.virtual_product_class))
        site_root = self.get_site_root()
        for path, cls in search_paths:
            try:
                resource = site_root.get_resource(path)
            except LookupError:
                continue
            else:
                # Return the real path and wrap into our virtual class
                return resource.get_canonical_path(), cls(resource.metadata)
        raise LookupError


    def get_canonical_path(self):
        """Get the real abspath from the shop.
        """
        path, resource = self.get_canonical_path_and_resource(self.name)
        return path


    def _get_resource(self, name):
        """Get the real resource from the shop.
        """
        path, resource = self.get_canonical_path_and_resource(name)
        return resource



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
    browse_content = Folder_BrowseContent(access=False)
    preview_content = Folder_PreviewContent(access=False)
    new_resource = Folder_NewResource(access=False)
    last_changes = Folder_LastChanges(access=False)
    orphans = Folder_Orphans(access=False)

    # XXX do NOT implement "_get_names"
    # The virtual categories must NOT be indexed as real resources


    def _get_resource(self, name):
        site_root = self.get_site_root()
        category = site_root.get_resource('shop/categories/%s' % name)
        metadata = category.metadata
        # Build another instance with the same properties
        return self.virtual_category_class(metadata)




register_resource_class(Categorie)
register_resource_class(Categories)
register_resource_class(VirtualCategories)
