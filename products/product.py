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
from itools.datatypes import String
from itools.gettext import MSG
from itools.handlers import merge_dicts
from itools.xapian import KeywordField
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from shop
from product_views import Product_View, Product_Edit, Product_EditModel, Product_Images
from product_views import Product_NewInstance, Product_AddToCart
from schema import product_schema



class Product(Folder):

    class_id = 'product'
    class_title = MSG(u'Product')
    class_views = ['view', 'edit', 'edit_model', 'images']

    new_instance = Product_NewInstance()
    view = Product_View()
    edit = Product_Edit()
    edit_model = Product_EditModel()
    add_to_cart = Product_AddToCart()
    images = Product_Images()


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(), product_schema,
                           product_model=String)


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        Folder._make_resource(Folder, folder, '%s/images' % name,
                             body='', title={'en': 'Images'})



    def get_catalog_fields(self):
        return (Folder.get_catalog_fields(self)
                + [KeywordField('product_model')])


    def get_catalog_values(self):
        values = Folder.get_catalog_values(self)
        values['product_model'] = self.get_property('product_model')
        return values



    def get_product_model(self, context):
        product_model = self.get_property('product_model')
        if not product_model:
            return None
        shop = self.parent.parent
        return shop.get_resource('products-models/%s' % product_model)



    def get_namespace(self, context):
        ns = {}
        # Basic informations
        for key in product_schema.keys():
            ns[key] = self.get_property(key)
        # Specific product informations
        product_model = self.get_product_model(context)
        if product_model:
            ns.update(product_model.get_model_ns(self))
        else:
            ns['specific_dic'] = {}
            ns['specific_list'] = []
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


    def get_price(self):
        # XXX Add VAT
        return self.get_property('price')


    #######################################
    ## XXX Hack dynamic properties
    ## To FIX in 0.60
    #######################################
    def get_property_and_language(self, name, language=None):
        # Default property
        if name in Product.get_metadata_schema():
            return Folder.get_property_and_language(self, name, language)
        # Dynamic property
        context = get_context()
        product_model = self.get_product_model(context)
        product_model_schema = product_model.get_model_schema()
        properties = self.metadata.properties

        # Check the property exists
        datatype = product_model_schema[name]
        if name not in properties:
            default = datatype.get_default()
            return default, None
        # Get the value
        value = properties[name]

        # Monolingual property
        if not isinstance(value, dict):
            return value, None

        # Language negotiation
        if language is None:
            context = get_context()
            if context is None:
                language = None
            else:
                languages = [
                    k for k, v in value.items() if not datatype.is_empty(v) ]
                accept = context.accept_language
                language = accept.select_language(languages)
            # Default (FIXME pick one at random)
            if language is None:
                language = value.keys()[0]
            return value[language], language

        if language in value:
            return value[language], language
        return datatype.get_default(), None



class Products(Folder):

    class_id = 'products'
    class_title = MSG(u'Products')


    def get_document_types(self):
        return [Product]


register_resource_class(Product)
register_resource_class(Products)
