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

# Import from standard library
from random import shuffle

# Import from itools
from itools.datatypes import String, Tokens
from itools.gettext import MSG
from itools.handlers import merge_dicts
from itools.html import XHTMLFile
from itools.web import get_context
from itools.xapian import KeywordField, TextField, BoolField

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_Orphans
from ikaaro.folder_views import Folder_PreviewContent, Folder_LastChanges
from ikaaro.folder_views import GoToSpecificDocument, Folder_BrowseContent
from ikaaro.registry import register_resource_class

# Import from shop
from cross_selling import CrossSellingTable
from images import PhotoOrderedTable
from product_views import Product_NewInstance
from product_views import Product_View, Product_Edit, Product_EditModel#, Product_Images
from schema import product_schema


def get_namespace_image(image, context):
    namespace = {'href': context.get_link(image),
                 'title': image.get_property('title')}
    return namespace



class ImagesFolder(Folder):

    class_id = 'images-folder'
    class_title = MSG(u'Images folder')

    def get_document_types(self):
        return [Image]


    # Views
    browse_content = Folder_BrowseContent(access='is_admin')
    preview_content = Folder_PreviewContent(access='is_admin')
    last_changes = Folder_LastChanges(access='is_admin')
    orphans = Folder_Orphans(access='is_admin')



class Product(Folder):

    class_id = 'product'
    class_title = MSG(u'Product')
    class_views = ['view', 'edit', 'edit_model', 'images', 'order',
                   'edit_cross_selling']
    class_version = '20090410'

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['images',
                                                      'order-photos',
                                                      'cross-selling']

    # Views
    new_instance = Product_NewInstance()
    view = Product_View()
    edit = Product_Edit()
    edit_model = Product_EditModel()
    #images = Product_Images()
    order = GoToSpecificDocument(specific_document='order-photos',
                                 title=MSG(u'Order photos'),
                                 access='is_admin')
    edit_cross_selling = GoToSpecificDocument(
            specific_document='cross-selling',
            title=MSG(u'Éditer la vente croisée'))


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(), product_schema,
                           product_model=String)


    def get_dynamic_metadata_schema(self, context):
        product_model = self.get_product_model(context)
        product_model_schema = product_model.get_model_schema()
        return merge_dicts(Folder.get_metadata_schema(), product_schema,
                            product_model_schema)


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Images folder
        ImagesFolder._make_resource(ImagesFolder, folder,
                                    '%s/images' % name, body='',
                                    title={'en': 'Images'})
        # Order images table
        PhotoOrderedTable._make_resource(PhotoOrderedTable, folder,
                                         '%s/order-photos' % name,
                                         title={'en': u'Order photos'})
        # Cross Selling table
        CrossSellingTable._make_resource(CrossSellingTable, folder,
                                         '%s/cross-selling' % name,
                                         title={'en': u'Cross selling'})


    def get_catalog_fields(self):
        return (Folder.get_catalog_fields(self)
                + [KeywordField('product_model'),
                   KeywordField('categories', is_stored=True),
                   TextField('html_description'),
                   TextField('description'),
                   BoolField('has_categories')])


    def get_catalog_values(self):
        values = Folder.get_catalog_values(self)
        values['product_model'] = self.get_property('product_model')
        # categories
        categories = []
        for category in self.get_property('categories'):
            segments = category.split('/')
            for i in range(len(segments)):
                categories.append('/'.join(segments[:i+1]))
        values['categories'] = categories
        values['has_categories'] = len(categories) != 0
        # HTML description XXX We must to_text API in itools ?
        doc = XHTMLFile()
        doc.events = self.get_property('html_description')
        values['html_description'] = doc.to_text()
        # description
        values['description'] = self.get_property('description')
        return values


    def get_canonical_path(self):
        site_root = self.get_site_root()
        products = site_root.get_resource('shop/products')
        return products.get_canonical_path().resolve2(self.name)


    def get_product_model(self, context):
        product_model = self.get_property('product_model')
        if not product_model:
            return None
        shop = self.get_real_resource().parent.parent
        return shop.get_resource('products-models/%s' % product_model)


    ##################################################
    ## Namespace
    ##################################################
    def get_small_namespace(self, context):
        namespace = {'name': self.name,
                     'href': context.get_link(self)}
        for key in ['title', 'description']:
            namespace[key] = self.get_property(key)
        namespace['cover'] = self.get_cover_namespace(context)
        return namespace


    def get_namespace(self, context):
        namespace = {}
        # Basic informations
        namespace['href'] = context.get_link(self)
        for key in product_schema.keys():
            namespace[key] = self.get_property(key)
        # Specific product informations
        product_model = self.get_product_model(context)
        if product_model:
            namespace.update(product_model.get_model_ns(self))
            purchase_options = product_model.get_purchase_options(self)
            namespace['purchase_options'] = purchase_options
        else:
            namespace['purchase_options'] = []
            namespace['specific_dic'] = {}
            namespace['specific_list'] = []
        # Complementaty Product
        complementary_products = self.get_ns_other_products(context)
        namespace['complementary_products'] = complementary_products
        # Cover
        namespace['cover'] = self.get_cover_namespace(context)
        # Images
        namespace['images'] = self.get_images_namespace(context)
        # Product is buyable
        namespace['is_buyable'] = self.is_buyable()
        # Authentificated ?
        ac = self.get_access_control()
        namespace['is_authenticated'] = ac.is_authenticated(context.user,
                                                            self)
        return namespace


    def get_ns_other_products(self, context):
        products = self.get_real_resource().parent
        selected_products = []
        selection = list(products.get_resources())
        shuffle(selection)
        for product in selection[0:5]:
            ns = product.get_small_namespace(context)
            selected_products.append(ns)
        return selected_products


    #####################
    # Images
    #####################
    def get_cover_namespace(self, context):
        cover = self.get_ordered_photos(context, quantity=1)
        if not cover:
            return None
        return get_namespace_image(cover[0], context)


    def get_images_namespace(self, context):
        ns_images = []
        for i, image in enumerate(self.get_ordered_photos(context)):
            # Ignore cover
            if i==0:
                continue
            ns_image = get_namespace_image(image, context)
            ns_images.append(ns_image)
        return ns_images


    def get_ordered_photos(self, context, quantity=None):
        # Search photos
        order = self.get_resource('order-photos')
        ordered_names = list(order.get_ordered_names())
        # If no photos, return
        if not ordered_names:
            return []
        # Get photos 
        images = []
        ac = self.get_access_control()
        user = context.user
        if quantity is None:
            quantity = len(ordered_names)
        for name in ordered_names[0:quantity]:
            image = order.get_resource(name)
            if ac.is_allowed_to_view(user, image):
                images.append(image)
        return images


    #####################
    ## API
    #####################
    def is_buyable(self):
        price = self.get_price()
        return float(price) != 0.0


    def get_price(self):
        # XXX Add VAT
        return self.get_property('price')


    #######################################
    ## XXX Hack dynamic properties
    ## To FIX in 0.60
    #######################################
    def get_property_and_language(self, name, language=None):
        # Default property
        value = Folder.get_property_and_language(self, name, language)
        if name in Product.get_metadata_schema():
            return value
        # Dynamic property
        context = get_context()
        product_model = self.get_product_model(context)
        product_model_schema = product_model.get_model_schema()
        datatype = product_model_schema[name]

        value, lang = value
        # FIXME Default value
        if value is None:
            return datatype.get_default(), lang
        # FIXME Multiple
        is_multiple = getattr(datatype, 'multiple', False)
        if is_multiple:
            if not isinstance(value, list):
                # Enumerate.get_namespace claims a single value or a list
                value = list(Tokens.decode(value))

        return datatype.decode(value), lang


    def set_property(self, name, value, language=None):
        context = get_context()
        # We have to reindex
        context.server.change_resource(self)
        # Dynamic property
        product_model = self.get_product_model(context)
        if not product_model:
            Folder.set_property(self, name, value, language)
            return
        product_model_schema = product_model.get_model_schema()
        if name in product_model_schema:
            datatype = product_model_schema[name]
            is_multiple = getattr(datatype, 'multiple', False)
            if is_multiple:
                self.metadata.properties[name] = Tokens.encode(value)
            else:
                Folder.set_property(self, name, datatype.encode(value), language)
            return

        # Default property
        Folder.set_property(self, name, value, language)


    def get_links(self):
        links = []
        real_resource = self.get_real_resource()
        shop = real_resource.parent.parent
        categories = shop.get_resource('categories')
        categories_path = categories.get_abspath()
        for categorie in self.get_property('categories'):
            links.append(str(categories_path.resolve2(categorie)))
        return links


    def change_link(self, old_path, new_path):
        real_resource = self.get_real_resource()
        shop = real_resource.parent.parent
        categories = shop.get_resource('categories')
        categories_path = categories.get_abspath()

        old_name = str(categories_path.get_pathto(old_path))
        new_name = str(categories_path.get_pathto(new_path))

        old_categories = self.get_property('categories')
        new_categories = []
        for name in self.get_property('categories'):
            if name == old_name:
                new_categories.append(new_name)
            else:
                new_categories.append(name)
        self.set_property('categories', new_categories)
        get_context().server.change_resource(self)


    #######################
    ## Updates methods
    #######################
    def update_20090327(self):
        from images import PhotoOrderedTable
        PhotoOrderedTable._make_resource(PhotoOrderedTable, self.handler,
                                         'order-photos',
                                         title={'en': u"Order photos"})


    def update_20090409(self):
        folder = self.get_resource('images')
        metadata = folder.metadata
        metadata.format = ImagesFolder.class_id
        metadata.version = ImagesFolder.class_version
        metadata.set_changed()


    def update_20090410(self):
        # Add the cross selling table
        if self.has_resource('cross-selling') is False:
            CrossSellingTable.make_resource(CrossSellingTable, self,
                                            'cross-selling')



class Products(Folder):

    class_id = 'products'
    class_title = MSG(u'Products')
    class_views = ['browse_content']

    # Views
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')


    def get_document_types(self):
        return [Product]



# Hack
CrossSellingTable.orderable_classes = Product

register_resource_class(ImagesFolder)
register_resource_class(Product)
register_resource_class(Products)
