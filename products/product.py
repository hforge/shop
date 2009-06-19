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
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument, Folder_BrowseContent
from ikaaro.registry import register_resource_class, register_field

# Import from shop
from cross_selling import CrossSellingTable
from dynamic_folder import DynamicFolder
from images import PhotoOrderedTable, ImagesFolder
from product_views import Product_NewInstance, Products_View, Product_ViewBox
from product_views import Product_View, Product_Edit, Product_EditModel
from schema import product_schema
from taxes import TaxesEnumerate
from shop.editable import Editable
from shop.utils import get_shop, format_price


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
    class_version = '20090619'

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
    viewbox = Product_ViewBox()


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(DynamicFolder.get_metadata_schema(),
                           Editable.get_metadata_schema(),
                           product_schema,
                           product_model=String)


    @staticmethod
    def _make_resource(cls, folder, name, ctime=None, *args, **kw):
        if ctime is None:
            ctime = datetime.now()
        DynamicFolder._make_resource(cls, folder, name, ctime=ctime, *args,
                                     **kw)
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
        values = merge_dicts(DynamicFolder._get_catalog_values(self),
                             Editable._get_catalog_values(self))
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
        # Images
        order = self.get_resource('order-photos')
        ordered_names = list(order.get_ordered_names())
        values['has_images'] = (len(ordered_names) != 0)
        # Product description
        values['description'] = self.get_property('description')
        # Creation time
        ctime = self.get_property('ctime')
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
        if not categories:
            return None
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
                     'price-with-tax': self.get_price_with_tax(),
                     'cover': self.get_cover_namespace(context)}
        for key in ['title', 'description']:
            namespace[key] = self.get_property(key)
        return namespace


    def get_cross_selling_namespace(self, context):
        cross_selling = []
        categories = self.get_real_resource().parent
        products = get_shop(self).get_resource('products')
        table = self.get_resource('cross-selling').handler
        viewbox = self.viewbox
        for id in table.get_record_ids_in_order():
            record = table.get_record(id)
            path = table.get_record_value(record, 'name')
            product = categories.get_resource(path)
            cross_selling.append(viewbox.GET(product, context))
        return cross_selling


    def get_namespace(self, context):
        namespace = {}
        # Get basic informations
        namespace['href'] = context.get_link(self)
        for key in product_schema.keys():
            if key=='data':
                continue
            namespace[key] = self.get_property(key)
        # Price
        namespace['price-with-tax'] = self.get_price_with_tax()
        # Data
        namespace['data'] = self.get_xhtml_data()
        # Specific product informations
        model = self.get_product_model()
        if model:
            namespace.update(model.get_model_ns(self))
        else:
            namespace['specific_dict'] = {}
            namespace['specific_list'] = []
        # Data
        namespace['data'] = self.get_xhtml_data()
        # Images
        namespace['images'] = self.get_images_namespace(context)
        # Product is buyable
        namespace['is_buyable'] = self.is_buyable()
        # Cross selling
        namespace['cross_selling'] = self.get_cross_selling_namespace(context)
        # Authentificated ?
        ac = self.get_access_control()
        namespace['is_authenticated'] = ac.is_authenticated(context.user, self)
        return namespace


    #####################
    # Images
    #####################
    def get_cover_namespace(self, context):
        cover = self.get_property('cover')
        if not cover:
            return
        image = self.get_resource(cover)
        return {'href': context.get_link(image),
                'title': image.get_property('title'),
                'is_cover': True}


    def get_images_namespace(self, context):
        namespace = []
        # Cover
        cover = self.get_cover_namespace(context)
        if cover:
            namespace = [cover]
        # Other images
        for image in self.get_ordered_photos(context):
            namespace.append({'href': context.get_link(image),
                              'title': image.get_property('title'),
                              'is_cover': False})
        return namespace


    def get_ordered_photos(self, context):
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
        for name in ordered_names:
            image = order.get_resource(name)
            if ac.is_allowed_to_view(user, image):
                images.append(image)
        return images


    #####################
    ## API
    #####################
    def is_buyable(self):
        return self.get_property('pre-tax-price') != decimal(0)


    def get_price_without_tax(self):
        return format_price(self.get_property('pre-tax-price'))


    def get_price_with_tax(self):
        price = self.get_property('pre-tax-price')
        tax = self.get_property('tax')
        price = price * (TaxesEnumerate.get_value(tax)/decimal(100) + 1)
        return format_price(price)


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


    def update_20090511(self):
        """ Update Unicode properties: add language "fr" if not already set"""
        model = self.get_product_model()
        if model:
            model_schema = model.get_model_schema()
        else:
            model_schema = {}
        schema = merge_dicts(Product.get_metadata_schema(), model_schema)
        for name, datatype in schema.items():
            if not getattr(datatype, 'multilingual', False):
                continue
            properties = self.metadata.properties
            if name not in properties:
                continue
            value = properties[name]
            if isinstance(value, dict):
                continue
            self.del_property(name)
            self.set_property(name, value, 'fr')
        # Replace html_description by data
        description = self.get_property('html_description')
        # Delete property
        self.del_property('html_description')
        if description and description.strip():
            self.set_property('data', description, language='fr')


    def update_20090514(self):
        """Add ctime property"""
        if self.get_property('ctime') is None:
            self.set_property('ctime', datetime.now())


    def update_20090619(self):
        """Bind the old product's cover management with the new one
        """
        order = self.get_resource('order-photos')
        order_handler = order.get_handler()
        records = list(order_handler.get_records_in_order())

        # If no photos, return
        if not records:
            return

        abspath = self.get_abspath()
        order_path = order.get_abspath()
        image_path = order_handler.get_record_value(records[0], 'name')
        real_image_path = order_path.resolve2(image_path)
        new_image_path = abspath.get_pathto(real_image_path)
        self.set_property('cover', new_image_path)



class Products(Folder):

    class_id = 'products'
    class_title = MSG(u'Products')
    class_views = ['view', 'browse_content']

    # Views
    view = Products_View()
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')


    def get_document_types(self):
        return [Product]



# XXX Hack (Demander à henry ?)
CrossSellingTable.orderable_classes = Product

# Register fields
register_field('product_model', String(is_indexed=True))
register_field('categories', String(is_indexed=True, multiple=True))
register_field('description', Unicode(is_indexed=True))
register_field('has_categories', Boolean(is_indexed=True))
register_field('has_images', Boolean(is_indexed=True))
register_field('ctime', String(is_indexed=True, is_stored=True))

# Register resources
register_resource_class(Product)
register_resource_class(Products)
