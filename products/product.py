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
from json import dumps

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, String, Unicode, Enumerate, DateTime
from itools.datatypes import Integer
from itools.gettext import MSG
from itools.uri import Path
from itools.web import get_context
from itools.xml import TEXT

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import SelectWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.utils import reduce_string
from ikaaro.workflow import WorkflowAware

# Import from shop
from cross_selling import CrossSellingTable
from declination import Declination
from dynamic_folder import DynamicFolder
from images import PhotoOrderedTable, ImagesFolder
from product_views import Product_NewProduct, Products_View, Product_ViewBox
from product_views import Product_View, Product_Edit, Product_AddLinkFile
from product_views import Product_Delete, Product_ImagesSlider
from product_views import Product_Print, Product_SendToFriend
from product_views import Product_Declinations, Products_ChangeCategory
from product_views import Product_ChangeProductModel, Products_Stock
from schema import product_schema
from taxes import TaxesEnumerate
from shop.cart import ProductCart
from shop.editable import Editable
from shop.enumerate_table import EnumerateTable_to_Enumerate
from shop.enumerate_table import Restricted_EnumerateTable_to_Enumerate
from shop.manufacturers import ManufacturersEnumerate
from shop.stock.stock_views import Stock_FillStockOut, Stock_Resupply
from shop.utils import get_shop, format_price, ShopFolder, generate_barcode


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


mail_stock_subject_template = MSG(u'Product out of stock')

mail_stock_body_template = MSG(u"""Hi,
The product {product_title} is out of stock\n
  {product_uri}\n
""")



class Product(WorkflowAware, Editable, DynamicFolder):

    class_id = 'product'
    class_title = MSG(u'Product')
    class_views = ['view', 'edit', 'declinations', 'images',
                   'order', 'edit_cross_selling', 'delete_product']
    class_description = MSG(u'A product')
    class_version = '20091123'

    ##################
    # Configuration
    ##################
    slider_view = Product_ImagesSlider()
    viewbox = Product_ViewBox()
    cross_selling_viewbox = Product_ViewBox()
    ##################


    __fixed_handlers__ = DynamicFolder.__fixed_handlers__ + ['images',
                                                      'order-photos',
                                                      'cross-selling']

    #######################
    # Views
    #######################
    view = Product_View()
    edit = Product_Edit()
    add_link_file = Product_AddLinkFile()
    change_product_model = Product_ChangeProductModel()
    declinations = Product_Declinations()
    order = GoToSpecificDocument(specific_document='order-photos',
                                 title=MSG(u'Manage photos'),
                                 access='is_allowed_to_edit')
    print_product = Product_Print()
    send_to_friend = Product_SendToFriend()
    edit_cross_selling = GoToSpecificDocument(
            specific_document='cross-selling',
            title=MSG(u'Edit cross selling'),
            access='is_allowed_to_edit')
    delete_product = Product_Delete()



    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(DynamicFolder.get_metadata_schema(),
                           Editable.get_metadata_schema(),
                           WorkflowAware.get_metadata_schema(),
                           product_schema)


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
        # Reference
        values['reference'] = self.get_property('reference')
        # Manufacturer
        values['manufacturer'] = self.get_property('manufacturer')
        # Supplier
        values['supplier'] = self.get_property('supplier')
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
        # Price # XXX We can't sort decimal, so transform to int
        values['stored_price'] = int(self.get_property('pre-tax-price') * 100)
        # Creation time
        values['ctime'] = self.get_property('ctime')
        # Is buyable ?
        values['is_buyable'] = self.is_buyable()

        return values


    def get_dynamic_schema(self):
        product_model = self.get_product_model()
        if not product_model:
            return {}
        return product_model.get_model_schema()



    def get_product_model(self):
        product_model = self.get_property('product_model')
        if not product_model:
            return None
        product = self.get_real_resource()
        shop = get_shop(product)
        return shop.get_resource('products-models/%s' % product_model)


    def to_text(self):
        result = {}
        languages = self.get_site_root().get_property('website_languages')
        product_model = self.get_product_model()
        schema = None
        if product_model:
            schema = product_model.get_model_schema()

        for language in languages:
            texts = result.setdefault(language, [])
            for key in ('title', 'description'):
                value = self.get_property(key, language=language)
                if value:
                    texts.append(value)

            # data (html)
            events = self.get_xhtml_data(language=language)
            text = [ unicode(value, 'utf-8') for event, value, line in events
                     if event == TEXT ]
            if text:
                texts.append(u' '.join(text))

            # Dynamic properties
            if schema is None:
                continue
            for key, datatype in schema.iteritems():
                value = self.get_property(key)
                if value:
                    text = None
                    multiple = datatype.multiple
                    if issubclass(datatype, Unicode):
                        if multiple:
                            text = ' '.join([ x for x in value ])
                        else:
                            text = value
                    elif issubclass(datatype, String):
                        if multiple:
                            text = ' '.join([ Unicode.decode(x)
                                              for x in value ])
                        else:
                            text = Unicode.decode(value)
                    elif issubclass(datatype, Enumerate):
                        values = value
                        if multiple is False:
                            values = [value]
                        # XXX use multilingual label
                        text = ' '.join(values)
                    if text:
                        texts.append(text)

        # Join
        for language, texts in result.iteritems():
            result[language] = u'\n'.join(texts)

        return result


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
            # If there is no category attached to the product
            # Just return his absolute path
            return self.get_abspath()
        category = categories[0]
        path = '../../categories/%s/%s' % (category, self.name)
        return self.get_abspath().resolve(path)


    ##################################################
    ## Purchase options
    ##################################################

    def get_purchase_options_names(self):
        """
        Return list of enumerates name corresponding to a purchase option
        (from the enumerates library)
        """
        model = self.get_product_model()
        if model is None:
            return []
        return model.get_property('declinations_enumerates')


    def get_purchase_options_schema(self):
        schema = {}
        for name in self.get_purchase_options_names():
            schema[name] = EnumerateTable_to_Enumerate(enumerate_name=name)
        return schema


    def get_javascript_namespace(self, declinations):
        # XXX
        # We have to Add price without tax (Before and after reduction)
        manage_stock = self.get_stock_option() != 'accept'
        purchase_options_names = self.get_purchase_options_names()
        # Base product
        stock_quantity = self.get_property('stock-quantity')
        products = {'base_product':
            {'price': format_price(self.get_price_with_tax()),
             'weight': str(self.get_weight()),
             'option': {},
             'stock': stock_quantity if manage_stock else None}}
        # Other products (declinations)
        for declination in declinations:
            stock_quantity = declination.get_quantity_in_stock()
            price = self.get_price_with_tax(id_declination=declination.name)
            products[declination.name] = {
              'price': format_price(price),
              'weight': str(declination.get_weight()),
              'option': {},
              'stock': stock_quantity if manage_stock else None}
            for name in purchase_options_names:
                value = declination.get_property(name)
                products[declination.name]['option'][name] = value
        return dumps(products)


    def get_purchase_options_namespace(self, declinations):
        namespace = []
        shop = get_shop(self)
        purchase_options_names = self.get_purchase_options_names()
        values = {}
        # Has declination ?
        if not declinations:
            return namespace
        # Get uniques purchase option values
        for declination in declinations:
            for name in purchase_options_names:
                value = declination.get_property(name)
                if not values.has_key(name):
                    values[name] = set([])
                values[name].add(value)
        # Build datatype / widget
        enumerates_folder = shop.get_resource('enumerates')
        for name in purchase_options_names:
            enumerate_table = enumerates_folder.get_resource(name)
            datatype = Restricted_EnumerateTable_to_Enumerate(
                          enumerate_name=name, values=values[name])
            widget = SelectWidget(name, has_empty_option=False)
            namespace.append(
                {'title': enumerate_table.get_title(),
                 'html': widget.to_html(datatype, None)})
        return namespace


    def get_declination(self, kw):
        """
        Return the name of declination corresponding to a
        dict of purchase options
        Example:
        {'color': 'red',
         'size': 'M'}
        ==> Return name of declination if exist
        ==> Return None if not exist
        """
        purchase_options_schema = self.get_purchase_options_schema()
        for declination in self.search_resources(cls=Declination):
            value = [kw[x] == declination.get_property(x)
                        for x in purchase_options_schema]
            if set(value) == set([True]):
                return declination.name
        return None


    def get_declination_namespace(self, declination_name):
        namespace = []
        shop = get_shop(self)
        declination = self.get_resource(declination_name)
        enumerates_folder = shop.get_resource('enumerates')
        for name in self.get_purchase_options_names():
            value = declination.get_property(name)
            enumerate_table = enumerates_folder.get_resource(name)
            datatype = EnumerateTable_to_Enumerate(enumerate_name=name)
            namespace.append({'title': enumerate_table.get_title(),
                              'value': datatype.get_value(value)})
        return namespace



    ##################################################
    ## Namespace
    ##################################################
    def get_small_namespace(self, context):
        shop = get_shop(self)
        abspath = context.resource.get_abspath()
        title = self.get_property('title')
        namespace = {
          'name': self.name,
          'title': title,
          'mini-title': reduce_string(title, shop.product_title_word_treshold),
          'href': abspath.get_pathto(self.get_virtual_path()),
          'cover': self.get_cover_namespace(context),
          'price': self.get_price_namespace(),
          'description': self.get_property('description'),
          'reference': self.get_property('reference')}
        # XXX Manufacturer (We should optimize)
        manufacturer = self.get_property('manufacturer')
        if manufacturer:
            namespace['manufacturer'] = ManufacturersEnumerate.get_value(
                                            manufacturer)
        else:
            namespace['manufacturer'] = None
        return namespace


    def get_price_namespace(self):
        has_reduction = self.get_property('reduction') > decimal(0)
        ns = {'with_tax': self.get_price_with_tax(pretty=True),
              'without_tax':  self.get_price_without_tax(pretty=True),
              'has_reduction': has_reduction}
        if has_reduction:
            kw = {'pretty': True, 'with_reduction': False}
            ns['with_tax_before_reduction'] = self.get_price_with_tax(**kw)
            ns['without_tax_before_reduction'] = self.get_price_with_tax(**kw)
        return ns


    def get_cross_selling_namespace(self, context):
        from shop.categories import Category

        table = self.get_resource('cross-selling')
        viewbox = self.cross_selling_viewbox
        cross_selling = []
        real_resource = self.get_real_resource()
        abspath = real_resource.get_abspath()
        products = real_resource.parent
        parent = self.parent
        if isinstance(parent, Category):
            current_category = parent.get_unique_id()
        else:
            current_category = self.get_property('categories')

        cross_products = table.get_products(context, self.class_id,
                                            products, [current_category],
                                            [abspath])
        for product in cross_products:
            cross_selling.append(viewbox.GET(product, context))
        return cross_selling


    def get_namespace(self, context):
        root = context.root
        namespace = {'name': self.name,
                     'price': self.get_price_namespace()}
        # Get basic informations
        abspath = context.resource.get_abspath()
        namespace['href'] = abspath.get_pathto(self.get_virtual_path())
        for key in product_schema.keys():
            if key=='data':
                continue
            namespace[key] = self.get_property(key)
        # Manufacturer
        manufacturer = self.get_property('manufacturer')
        if manufacturer:
            manufacturer = root.get_resource(manufacturer)
            namespace['manufacturer'] = {'name': manufacturer.name,
                                         'title': manufacturer.get_title()}
        else:
            namespace['manufacturer'] = None
        # Data
        namespace['data'] = self.get_xhtml_data()
        # Specific product informations
        model = self.get_product_model()
        if model:
            namespace.update(model.get_model_namespace(self))
        else:
            namespace['specific_dict'] = {}
            namespace['specific_list'] = []
        # Images
        namespace['cover'] = self.get_cover_namespace(context)
        namespace['images'] = self.get_images_namespace(context)
        namespace['has_more_than_one_image'] = len(namespace['images']) > 1
        # Slider
        namespace['images-slider'] = self.slider_view.GET(self, context)
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
        image = None
        if cover:
            image = self.get_resource(cover, soft=True)
        if not image:
            model = self.get_product_model()
            if model is None:
                return
            cover = model.get_property('default_cover')
            if cover:
                image = model.get_resource(cover, soft=True)
            else:
                return
            if not image:
                return
        return {'href': context.get_link(image),
                'uri': image.handler.uri,
                'title': image.get_property('title')}


    def get_images_namespace(self, context):
        images = []
        for image in self.get_ordered_photos(context):
            images.append({'href': context.get_link(image),
                           'title': image.get_property('title')})
        return images


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
            image = order.get_resource(name, soft=True)
            if image and ac.is_allowed_to_view(user, image):
                images.append(image)
        return images

    #####################
    ## Stock
    #####################

    def get_stock_option(self):
        # XXX Get option from shop generatl configuration
        return self.get_property('stock-option')


    def is_in_stock_or_ignore_stock(self, quantity):
        if self.get_stock_option() == 'accept':
            return True
        return self.get_property('stock-quantity') >= quantity


    def send_alert_stock(self):
        shop = get_shop(self)
        context = get_context()
        root = context.root
        product_uri = context.uri.resolve('/shop/products/%s/' % self.name)
        kw = {'product_title': self.get_title(), 'product_uri': product_uri}
        body = mail_stock_body_template.gettext(**kw)
        for to_addr in shop.get_property('order_notification_mails'):
            root.send_email(to_addr=to_addr,
                            subject=mail_stock_subject_template,
                            text=body)


    def remove_from_stock(self, quantity, id_declination=None):
        if id_declination:
            declination = self.get_resource(id_declination)
            declination.remove_from_stock(quantity)
        else:
            stock_option = self.get_stock_option()
            old_quantity = self.get_property('stock-quantity')
            new_quantity = old_quantity - quantity
            if new_quantity <= 0 and stock_option == 'accept':
                new_quantity = 0
            if new_quantity <= 0 and stock_option == 'refuse_go_private':
                self.set_property('state', 'private')
            if old_quantity > 0 and new_quantity == 0:
                self.send_alert_stock()
            self.set_property('stock-quantity', new_quantity)

    #####################
    ## API
    #####################
    def is_buyable(self, quantity=1):
        return (self.get_property('pre-tax-price') != decimal(0) and
                self.get_property('tax') is not None and
                self.get_property('is_buyable') is True and
                self.get_statename() == 'public' and
                self.is_in_stock_or_ignore_stock(quantity))


    def get_reference(self, id_declination=None):
        if id_declination:
            declination = self.get_resource(id_declination, soft=True)
            if declination:
                reference = declination.get_property('reference')
                if reference:
                    return reference
        return self.get_property('reference')


    def get_tax_value(self):
        shop = get_shop(self)
        # Get zone from cookie
        id_zone = ProductCart(get_context()).id_zone
        # If not define... get default zone
        if id_zone is None:
            id_zone = shop.get_property('shop_default_zone')
        # Check if zone has tax ?
        zones = shop.get_resource('countries-zones').handler
        zone_record = zones.get_record(int(id_zone))
        if zones.get_record_value(zone_record, 'has_tax') is True:
            tax = self.get_property('tax')
            tax_value = TaxesEnumerate.get_value(tax) or decimal(0)
            return (tax_value/decimal(100) + 1)
        return decimal(1)


    def get_price_without_tax(self, id_declination=None,
                               with_reduction=True, pretty=False):
        if id_declination:
            declination = self.get_resource(id_declination)
            price = declination.get_price_without_tax()
        else:
            price = self.get_property('pre-tax-price')
        # Reduction
        if with_reduction is True:
            price = price - self.get_property('reduction')
        # Format price
        if pretty is True:
            return format_price(price)
        return price


    def get_price_with_tax(self, id_declination=None,
                            with_reduction=True, pretty=False):
        price = self.get_price_without_tax(id_declination,
                    with_reduction=with_reduction)
        price = price * self.get_tax_value()
        # Format price
        if pretty is True:
            return format_price(price)
        return price


    def get_weight(self, id_declination=None):
        if id_declination:
            declination = self.get_resource(id_declination, soft=True)
            if declination:
                return declination.get_weight()
        return self.get_property('weight')


    def save_barcode(self, reference):
        shop = get_shop(self)
        barcode = generate_barcode(shop.get_property('barcode_format'),
                                   reference)
        self.del_resource('barcode', soft=True)
        metadata =  {'title': {'en': u'Barcode'},
                     'filename': 'barcode.png',
                     'format': 'image/png'}
        Image.make_resource(Image, self, 'barcode', body=barcode, **metadata)



    #########################################
    # Update links mechanism
    #-------------------------
    #
    # If a user rename a category we have
    # to update categories associated to products
    #
    #########################################

    def get_links(self):
        links = Editable.get_links(self)
        links += DynamicFolder.get_links(self)
        real_resource = self.get_real_resource()
        shop = get_shop(real_resource)
        # categories
        categories = shop.get_resource('categories')
        categories_path = categories.get_abspath()
        for categorie in self.get_property('categories'):
            links.append(str(categories_path.resolve2(categorie)))
        # product model
        product_model = self.get_property('product_model')
        if product_model:
            shop_path = shop.get_abspath()
            full_path = shop_path.resolve2('products-models/%s' % product_model)
            links.append(str(full_path))
        # Cover
        cover = self.get_property('cover')
        if cover:
            base = self.get_canonical_path()
            links.append(str(base.resolve2(cover)))

        return links


    def update_links(self, old_path, new_path):
        Editable.update_links(self, old_path, new_path)
        DynamicFolder.update_links(self, old_path, new_path)

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

        # Cover
        cover = self.get_property('cover')
        if cover:
            base = self.get_canonical_path()
            if str(base.resolve2(cover)) == old_path:
                # Hit the old name
                new_path2 = base.get_pathto(Path(new_path))
                self.set_property('cover', str(new_path2))
        get_context().database.change_resource(self)


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


    def update_20090806(self):
        self.set_property('state', 'public')


    def update_20091123(self):
        reference = self.get_property('reference')
        self.save_barcode(reference)



class Products(ShopFolder):

    class_id = 'products'
    class_title = MSG(u'Products')
    class_views = ['browse_content', 'new_product']

    # Views
    browse_content = Products_View()
    stock = Products_Stock()
    stock_out = Stock_FillStockOut()
    stock_resupply = Stock_Resupply()
    new_product = Product_NewProduct()
    change_category = Products_ChangeCategory()


    def can_paste(self, source):
        return isinstance(source, Product)


    def get_document_types(self):
        return []



# Product class depents on CrossSellingTable class and vice versa
CrossSellingTable.orderable_classes = Product

# Register fields
register_field('reference', Unicode(is_indexed=True, is_stored=True))
register_field('manufacturer', Unicode(is_indexed=True))
register_field('supplier', Unicode(is_indexed=True, multiple=True))
register_field('product_model', String(is_indexed=True, is_stored=True))
register_field('categories', String(is_indexed=True, multiple=True, is_stored=True))
register_field('has_categories', Boolean(is_indexed=True)) # XXX Obsolete
register_field('has_images', Boolean(is_indexed=True, is_stored=True))
register_field('is_buyable', Boolean(is_indexed=True))
register_field('ctime', DateTime(is_stored=True, is_indexed=True))
# XXX xapian can't sort decimal
register_field('stored_price', Integer(is_indexed=False, is_stored=True))

# Register resources
register_resource_class(Product)
register_resource_class(Products)
