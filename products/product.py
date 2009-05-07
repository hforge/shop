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
from decimal import Decimal as decimal
from datetime import datetime

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, String, Unicode
from itools.gettext import MSG
from itools.vfs import get_ctime
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument, Folder_BrowseContent
from ikaaro.registry import register_resource_class, register_field

# Import from shop
from cross_selling import CrossSellingTable
from dynamic_folder import DynamicFolder
from images import PhotoOrderedTable, ImagesFolder
from product_views import Product_NewInstance
from product_views import Product_View, Product_Edit, Product_EditModel
from schema import product_schema
from shop.editable import Editable
from shop.utils import get_shop

###############
# TODO Future
###############
#
# => We can define OrderedContainer in itws (ofen used)
#    (method get_ordered_photos)
#
# => Events -> to_text API in Itools (see get_catalog_values)
#
#
#


class Product(Editable, DynamicFolder):

    class_id = 'product'
    class_title = MSG(u'Product')
    class_views = ['view', 'edit', 'edit_model', 'images', 'order',
                   'edit_cross_selling']
    class_version = '20090507'

    __fixed_handlers__ = DynamicFolder.__fixed_handlers__ + ['images',
                                                      'order-photos',
                                                      'cross-selling']

    #######################
    # Views
    #######################
    new_instance = Product_NewInstance()
    view = Product_View()
    edit = Product_Edit()
    edit_model = Product_EditModel()
    order = GoToSpecificDocument(specific_document='order-photos',
                                 title=MSG(u'Order photos'),
                                 access='is_allowed_to_edit')
    edit_cross_selling = GoToSpecificDocument(
            specific_document='cross-selling',
            title=MSG(u'Edit cross selling'),
            access='is_allowed_to_edit')


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(DynamicFolder.get_metadata_schema(),
                           Editable.get_metadata_schema(),
                           product_schema,
                           product_model=String)


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        DynamicFolder._make_resource(cls, folder, name, *args, **kw)
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


    def _get_catalog_values(self):
        values = merge_dicts(DynamicFolder.get_catalog_values(self),
                             Editable.get_catalog_values(self))
        # Product models
        values['product_model'] = self.get_property('product_model')
        # We index categories
        categories = []
        for category in self.get_property('categories'):
            segments = category.split('/')
            for i in range(len(segments)):
                categories.append('/'.join(segments[:i+1]))
        values['categories'] = categories
        values['has_categories'] = len(categories) != 0
        # Product description
        values['description'] = self.get_property('description')
        # Creation date
        try:
            ctime = get_ctime(self.metadata.uri)
        except OSError:
            # when creating ressource get_catalog_values is called before
            # commit
            ctime = datetime.now()
        values['ctime'] = ctime.strftime('%Y%m%d%H%M%S')

        return values


    def get_product_model(self):
        product_model = self.get_property('product_model')
        if not product_model:
            return None
        product = self.get_real_resource()
        shop = get_shop(product)
        return shop.get_resource('products-models/%s' % product_model)


    ####################################################
    # Get canonical /virtual paths.
    ####################################################

    def get_canonical_path(self):
        site_root = self.get_site_root()
        products = site_root.get_resource('shop/products')
        return products.get_canonical_path().resolve2(self.name)


    def get_virtual_path(self):
        """XXX hardcoded for values we have always used so far.
        Remember to change it if your virtual categories folder is named
        something else.
        """
        categories = self.get_property('categories')
        category = categories[0]
        path = '../../categories/%s/%s' % (category, self.name)
        return self.get_abspath().resolve(path)

    ##################################################
    ## Namespace
    ##################################################
    def get_small_namespace(self, context):
        # get namespace
        namespace = {'name': self.name,
                     'href': context.get_link(self),
                     'cover': self.get_cover_namespace(context)}
        for key in ['title', 'description']:
            namespace[key] = self.get_property(key)
        return namespace


    def get_namespace(self, context):
        namespace = {}
        # Get basic informations
        namespace['href'] = context.get_link(self)
        for key in product_schema.keys():
            if key=='data':
                continue
            namespace[key] = self.get_property(key)
        # Data
        namespace['data'] = self.get_xhtml_data()
        # Specific product informations
        model = self.get_product_model()
        if model:
            namespace.update(model.get_model_ns(self))
        else:
            namespace['specific_dict'] = {}
            namespace['specific_list'] = []
        # Images
        namespace['images'] = self.get_images_namespace(context)
        # Product is buyable
        namespace['is_buyable'] = self.is_buyable()
        # Authentificated ?
        ac = self.get_access_control()
        namespace['is_authenticated'] = ac.is_authenticated(context.user, self)
        return namespace


    #####################
    # Images
    #####################
    def get_cover_namespace(self, context):
        images = self.get_images_namespace(context, 1)
        if images:
            return images[0]
        return None


    def get_images_namespace(self, context, quantity=None):
        namespace = []
        for image in self.get_ordered_photos(context, quantity):
            namespace.append({'href': context.get_link(image),
                              'title': image.get_property('title')})
        return namespace


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
        return self.get_price() != decimal(0)


    def get_price(self):
        return self.get_property('price')


    def get_weight(self):
        return self.get_property('weight')


    def get_options_namespace(self, options):
        """
          Get:
              options = {'color': 'red',
                         'size': '1'}
          Return:
              namespace = [{'title': 'Color',
                            'value': 'Red'},
                           {'title': 'Size',
                            'value': 'XL'}]
        """
        product_model = self.get_product_model()
        return product_model.options_to_namespace(options)


    #########################################
    # Update links mechanism
    #-------------------------
    #
    # If a user rename a category we have
    # to update categories associated to products
    #
    #########################################

    def get_links(self):
        links = []
        real_resource = self.get_real_resource()
        shop = get_shop(real_resource)
        categories = shop.get_resource('categories')
        categories_path = categories.get_abspath()
        for categorie in self.get_property('categories'):
            links.append(str(categories_path.resolve2(categorie)))
        links += Editable.get_links(self)
        return links


    def change_link(self, old_path, new_path):
        real_resource = self.get_real_resource()
        shop = get_shop(real_resource)
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


    def update_20090507(self):
        """ Update Unicode properties: add language "fr" if not already set"""
        from itools.datatypes import Unicode
        model = self.get_product_model()
        if model:
            model_schema = model.get_model_schema()
        else:
            model_schema = {}
        schema = merge_dicts(Product.get_metadata_schema(), model_schema)
        for name, datatype in schema.items():
            if not issubclass(datatype, Unicode):
                continue
            properties = self.metadata.properties
            if name not in properties:
                continue
            value = properties[name]
            if isinstance(value, dict):
                continue
            self.del_property(name)
            self.set_property(name, value, 'fr')



class Products(Folder):

    class_id = 'products'
    class_title = MSG(u'Products')
    class_views = ['browse_content']

    # Views
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')


    def get_document_types(self):
        return [Product]



# XXX Hack (Demander à henry ?)
CrossSellingTable.orderable_classes = Product


# Register
register_field('product_model', String(is_indexed=True))
register_field('categories', String(is_indexed=True, multiple=True))
register_field('html_description', Unicode(is_indexed=True))
register_field('description', Unicode(is_indexed=True))
register_field('has_categories', Boolean(is_indexed=True))
register_field('ctime', String(is_indexed=True, is_stored=True))
register_resource_class(Product)
register_resource_class(Products)
