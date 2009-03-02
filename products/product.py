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

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from itools
from itools.datatypes import Boolean, Decimal, Enumerate, String, Tokens, Unicode
from itools.gettext import MSG

# Import from shop
from product_views import Product_View, Product_Edit, Product_EditSpecific, Product_Images
from schema import product_schema



class Product(Folder):

    class_id = 'product'
    class_title = MSG(u'Product')
    class_views = ['view', 'edit', 'edit_specific', 'images']

    view = Product_View()
    edit = Product_Edit()
    edit_specific = Product_EditSpecific()
    images = Product_Images()


    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema.update(product_schema)
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        Folder._make_resource(Folder, folder, '%s/images' % name,
                             body='', title={'en': 'Images'})



    def get_product_type(self, context):
        product_type = self.get_property('product_type')
        return context.root.get_resource('types/%s' % product_type)



    def get_namespace(self, context):
        ns = {}
        # Basic informations
        for key in product_schema.keys():
            ns[key] = self.get_property(key)
        # Specific product informations
        product_type = self.get_product_type(context)
        ns.update(product_type.get_producttype_ns(self))
        # Images
        ns.update(self.get_images_ns())
        return ns


    def get_images_ns(self):
        ns = {'images': []}
        folder_images = self.get_resource('images')
        for image in folder_images.get_resources():
            ns['images'].append({'href': image.abspath,
                                 'title': image.get_property('title')})
        return ns


class Products(Folder):

    class_id = 'products'
    class_title = MSG(u'Products')


    def get_document_types(self):
        return [Product]


register_resource_class(Product)
register_resource_class(Products)
