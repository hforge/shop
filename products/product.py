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
from itools.uri import resolve_uri2, Path
from itools.web import get_context
from itools.xml import TEXT

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import SelectWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.utils import reduce_string
from ikaaro.workflow import WorkflowAware

# Import from itws
from itws.tags import TagsAware

# Import from shop
from declination import Declination
from dynamic_folder import DynamicFolder, DynamicProperty
from images import PhotoOrderedTable, ImagesFolder
from product_views import Product_NewProduct, Products_View, Product_ViewBox
from product_views import Product_CrossSellingViewBox
from product_views import Product_View, Product_Edit, Product_AddLinkFile
from product_views import Product_Delete
from product_views import Product_Print, Product_SendToFriend
from product_views import Product_Declinations
from product_views import Product_ChangeProductModel, Products_Stock
from schema import product_schema
from taxes import TaxesEnumerate
from shop.cart import ProductCart
from shop.cross_selling import CrossSellingTable
from shop.editable import Editable
from shop.enumerate_table import EnumerateTable_to_Enumerate
from shop.enumerate_table import Restricted_EnumerateTable_to_Enumerate
from shop.manufacturers import ManufacturersEnumerate
from shop.modules import ModuleLoader
from shop.shop_views import Shop_Login, Shop_Register
from shop.stock.stock_views import Stock_FillStockOut, Stock_Resupply
from shop.utils import get_shop, format_price, ShopFolder, generate_barcode


mail_stock_subject_template = MSG(u'Product out of stock')

mail_stock_body_template = MSG(u"""Hi,
The product {product_title} is out of stock\n
  {product_uri}\n
""")


class Product(WorkflowAware, Editable, TagsAware, DynamicFolder):

    class_id = 'product'
    class_title = MSG(u'Product')
    class_description = MSG(u'A product')
    class_version = '20100429'

    ##################
    # Configuration
    ##################
    viewbox = Product_ViewBox()
    cross_selling_viewbox = Product_CrossSellingViewBox()
    ##################


    __fixed_handlers__ = DynamicFolder.__fixed_handlers__ + ['images',
                                                      'order-photos',
                                                      'cross-selling']

    #######################
    # Views
    #######################
    view = Product_View()
    login = Shop_Login()
    register = Shop_Register()
    tag_view = viewbox
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
    order_preview = viewbox



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
                             TagsAware._get_catalog_values(self),
                             Editable._get_catalog_values(self))
        # Reference
        values['reference'] = self.get_property('reference')
        # Manufacturer
        values['manufacturer'] = self.get_property('manufacturer')
        # Supplier
        values['supplier'] = self.get_property('supplier')
        # Product models
        values['product_model'] = self.get_property('product_model')
        # Images
        order = self.get_resource('order-photos')
        ordered_names = list(order.get_ordered_names())
        values['has_images'] = (len(ordered_names) != 0)
        # Price # XXX We can't sort decimal, so transform to int
        values['stored_price'] = int(self.get_price_with_tax() * 100)
        # Creation time
        values['ctime'] = self.get_property('ctime')
        # Promotion
        values['has_reduction'] = self.get_property('has_reduction')
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
        shop = get_shop(self)
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


    def get_resource_icon(self, size=16):
        context = get_context()
        size = 48
        cover = self.get_property('cover')
        link = '%s/%s' % (context.get_link(self), cover)
        return '%s/;thumb?width=%s&amp;height=%s' % (link, size, size)

    ####################################################
    # Get canonical /virtual paths.
    ####################################################

# XXX
#    def get_canonical_path(self):
#    def get_virtual_path(self):


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
        products = {}
        if len(declinations)==0:
            products['base_product'] = {
                'price': format_price(self.get_price_with_tax()),
                'weight': str(self.get_weight()),
                'option': {},
                'stock': stock_quantity if manage_stock else None}
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
        title = self.get_property('title')
        # Dynamic property
        dynamic_property = DynamicProperty()
        dynamic_property.resource = self
        # Category
        category = {'name': self.parent.name,
                    'href': context.get_link(self.parent),
                    'title': self.parent.get_title()}
        # Lang (usefull to show contextuel images)
        ws_languages = context.site_root.get_property('website_languages')
        accept = context.accept_language
        lang = accept.select_language(ws_languages)
        # Shop modules
        shop_module = ModuleLoader()
        shop_module.context = context
        shop_module.here = self
        # Return namespace
        return {
          'name': self.name,
          'lang': lang,
          'module': shop_module,
          'dynamic_property': dynamic_property,
          'category': category,
          'cover': self.get_cover_namespace(context),
          'description': self.get_property('description'),
          'href': context.get_link(self),
          'manufacturer': ManufacturersEnumerate.get_value( self.get_property('manufacturer')),
          'mini-title': reduce_string(title,
                                      shop.product_title_word_treshold,
                                      shop.product_title_phrase_treshold),
          'price': self.get_price_namespace(),
          'reference': self.get_property('reference'),
          'title': title}


    def get_price_namespace(self):
        has_reduction = self.get_property('has_reduction')
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
        abspath = self.get_abspath()
        parent = self.parent
        if isinstance(parent, Category):
            current_category = [parent]
        elif isinstance(self, Category):
            current_category = [self]
        else:
            current_category = []

        cross_products = table.get_products(context, self.class_id,
                                            current_category, [abspath])
        for product in cross_products:
            cross_selling.append(viewbox.GET(product, context))
        return cross_selling


    def get_namespace(self, context):
        root = context.root
        shop = get_shop(self)
        namespace = {'name': self.name,
                     'price': self.get_price_namespace()}
        # Get basic informations
        abspath = context.resource.get_abspath()
        namespace['href'] = context.get_link(self)
        for key in product_schema.keys():
            if key=='data':
                continue
            namespace[key] = self.get_property(key)
        # Category
        namespace['category'] = {'name': self.parent.name,
                                 'href': context.get_link(self.parent),
                                 'title': self.parent.get_title()}
        # Categorie XXX To remove
        namespace['categorie'] = self.parent.get_title()
        # Lang (usefull to show contextuel images)
        ws_languages = context.site_root.get_property('website_languages')
        accept = context.accept_language
        lang = accept.select_language(ws_languages)
        namespace['lang'] = lang
        # Manufacturer
        manufacturer = self.get_property('manufacturer')
        if manufacturer:
            manufacturer = root.get_resource(manufacturer)
            link = context.get_link(manufacturer)
            photo = manufacturer.get_property('photo')
            namespace['manufacturer'] = {
                'name': manufacturer.name,
                'link': link,
                'photo': resolve_uri2(link, photo),
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
        # Product is buyable
        namespace['is_buyable'] = self.is_buyable()
        # Cross selling
        namespace['cross_selling'] = self.get_cross_selling_namespace(context)
        # Authentificated ?
        ac = self.get_access_control()
        namespace['is_authenticated'] = ac.is_authenticated(context.user, self)
        # Shop modules
        shop_module = ModuleLoader()
        shop_module.context = context
        shop_module.here = self
        namespace['module'] = shop_module
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
            return
        return {'href': context.get_link(image),
                'key': image.handler.key,
                'title': image.get_property('title') or self.get_title()}


    def get_images_namespace(self, context):
        images = []
        for image in self.get_ordered_photos(context):
            images.append({'href': context.get_link(image),
                           'title': image.get_property('title') or self.get_title()})
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


    def is_in_stock_or_ignore_stock(self, quantity, id_declination=None):
        if self.get_stock_option() == 'accept':
            return True
        if id_declination:
            declination = self.get_resource(id_declination)
            resource = declination
        else:
            resource = self
        return resource.get_property('stock-quantity') >= quantity


    def send_alert_stock(self):
        shop = get_shop(self)
        context = get_context()
        root = context.root
        product_uri = context.uri.resolve('/shop/products/%s/' % self.name)
        kw = {'product_title': self.get_title(), 'product_uri': product_uri}
        body = mail_stock_body_template.gettext(**kw)
        for to_addr in shop.get_property('order_notification_mails'):
            root.send_email(to_addr=to_addr,
                            subject=mail_stock_subject_template.gettext(),
                            text=body)


    def remove_from_stock(self, quantity, id_declination=None):
        stock_option = self.get_stock_option()
        if stock_option == 'dont_handle':
            return
        resource = self
        if id_declination:
            declination = self.get_resource(id_declination)
            resource = declination
        old_quantity = resource.get_quantity_in_stock()
        new_quantity = old_quantity - quantity
        if old_quantity > 0 and new_quantity <= 0:
            self.send_alert_stock()
        resource.set_property('stock-quantity', new_quantity)
        # XXX If is declination go private ?
        if not id_declination and new_quantity <= 0 and stock_option == 'refuse_go_private':
            self.set_property('state', 'private')


    def add_on_stock(self, quantity, id_declination=None):
        stock_option = self.get_stock_option()
        if stock_option == 'dont_handle':
            return
        resource = self
        if id_declination:
            declination = self.get_resource(id_declination)
            resource = declination
        old_quantity = resource.get_property('stock-quantity')
        new_quantity = old_quantity + quantity
        resource.set_property('stock-quantity', new_quantity)


    def get_quantity_in_stock(self):
        return self.get_property('stock-quantity')

    #####################
    ## API
    #####################
    def is_buyable(self, quantity=1):
        return (self.get_price_without_tax() != decimal(0) and
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


    def get_price_prefix(self):
        context = get_context()
        user = context.user
        if (context.user and
            context.user.get_property('user_group') == 'group_pro'):
            return 'pro-'
        return ''


    def get_tax_value(self):
        shop = get_shop(self)
        prefix = self.get_price_prefix()
        # Get zone from cookie
        id_zone = ProductCart(get_context()).id_zone
        # If not define... get default zone
        if id_zone is None:
            id_zone = shop.get_property('shop_default_zone')
        # Check if zone has tax ?
        zones = shop.get_resource('countries-zones').handler
        zone_record = zones.get_record(int(id_zone))
        if zones.get_record_value(zone_record, 'has_tax') is True:
            tax = self.get_property('%stax'% prefix)
            tax_value = TaxesEnumerate.get_value(tax) or decimal(0)
            return (tax_value/decimal(100) + 1)
        return decimal(1)


    def get_price_without_tax(self, id_declination=None,
                               with_reduction=True, pretty=False):
        prefix = self.get_price_prefix()
        # Base price
        if with_reduction is True and self.get_property('%shas_reduction' % prefix):
            price = self.get_property('%sreduce-pre-tax-price' % prefix)
        else:
            price = self.get_property('%spre-tax-price' % prefix)
        # Declination
        if id_declination:
            declination = self.get_resource(id_declination)
            price = price + declination.get_price_impact()
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
        format = shop.get_property('barcode_format')
        barcode = generate_barcode(format, reference)
        if not barcode:
            return
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
        site_root = self.get_site_root()
        shop = site_root.get_resource('shop')
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
        # Tags
        tags_base = site_root.get_abspath().resolve2('tags')
        links.extend([str(tags_base.resolve2(tag))
                      for tag in self.get_property('tags')])
        # Manufacturer
        manufacturer = self.get_property('manufacturer')
        if manufacturer:
            links.append(manufacturer)

        return links


    def update_links(self, source, target):
        Editable.update_links(self, source, target)
        DynamicFolder.update_links(self, source, target)

        # Cover
        cover = self.get_property('cover')
        if cover:
            base = self.get_canonical_path()
            resources_new2old = get_context().database.resources_new2old
            base = str(base)
            old_base = resources_new2old.get(base, base)
            old_base = Path(old_base)
            new_base = Path(base)
            if str(old_base.resolve2(cover)) == source:
                # Hit the old name
                new_path = new_base.get_pathto(Path(target))
                self.set_property('cover', str(new_path))

        # Tags
        site_root = self.get_site_root()
        source_path = Path(source)
        tags_base = site_root.get_abspath().resolve2('tags')
        if tags_base.get_prefix(source_path) == tags_base:
            tags = list(self.get_property('tags'))
            source_name = source_path.get_name()
            target_name = Path(new_path).get_name()
            for tag in tags:
                if tag == source_name:
                    # Hit
                    index = tags.index(source_name)
                    tags[index] = target_name
                    self.set_property('tags', tags)

        # Manufacturer
        manufacturer = self.get_property('manufacturer')
        if manufacturer and manufacturer == source:
            self.set_property('manufacturer', str(target))

        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        Editable.update_relative_links(self, source)
        DynamicFolder.update_relative_links(self, source)

        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        # Cover
        cover = self.get_property('cover')
        if cover:
            # Calcul the old absolute path
            old_abs_path = source.resolve2(cover)
            # Check if the target path has not been moved
            new_abs_path = resources_old2new.get(old_abs_path,
                                                 old_abs_path)
            # Build the new reference with the right path
            # Absolute path allow to call get_pathto with the target
            new_path = str(target.get_pathto(new_abs_path))
            # Update the title link
            self.set_property('cover', str(new_path))

        # Manufacturer and categories (not needed, due to abspath)

    #######################
    ## Class views
    #######################
    def get_class_views(self):
        context = get_context()
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return ['edit', 'view'] + self.default_class_views
        return ['view', 'edit'] + self.default_class_views


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

    default_class_views = ['declinations', 'images',
                   'order', 'edit_cross_selling', 'delete_product']
    class_views = property(get_class_views, None, None, '')
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


    def update_20100119(self):
        """ Update to new reduction mechanism """
        reduction = self.get_property('reduction')
        if reduction:
            self.del_property('reduction')
            value = self.get_property('pre-tax-price') - reduction
            self.set_property('reduce-pre-tax-price', value)
            self.set_property('has_reduction', True)


    def update_20100429(self):
        """Add the handle-stock boolean"""
        print 'updating', self
        self.set_property('stock-handled', True)


class Products(ShopFolder):

    class_id = 'products'
    class_title = MSG(u'Products')
    class_views = ['browse_content', 'new_product']
    class_version = '20100229'

    # Views
    browse_content = Products_View()
    stock = Products_Stock()
    stock_out = Stock_FillStockOut()
    stock_resupply = Stock_Resupply()
    new_product = Product_NewProduct()


    def can_paste(self, source):
        return isinstance(source, Product)


    def get_document_types(self):
        return []


    def update_20100229(self):
        """ Now a product has only one category """
        shop = get_shop(self)
        for resource in self.get_resources():
            if not isinstance(resource, Product):
                continue
            categories = resource.get_property('categories')
            if categories is None:
                new_path = '../../categories/%s' % resource.name
            elif len(categories) > 1:
                category = categories[0]
                new_path = '../../categories/%s/%s' % (category, resource.name)
            elif len(categories) == 1:
                category = categories[0]
                new_path = '../../categories/%s/%s' % (category, resource.name)
            print '=================='
            print resource.get_abspath()
            print '===>', new_path
            self.move_resource(resource.name, new_path)
            print '=================='




# Product class depents on CrossSellingTable class and vice versa
CrossSellingTable.orderable_classes = Product

# Register fields
register_field('reference', String(is_indexed=True, is_stored=True))
register_field('manufacturer', Unicode(is_indexed=True))
register_field('supplier', Unicode(is_indexed=True, multiple=True))
register_field('product_model', String(is_indexed=True, is_stored=True))
register_field('has_images', Boolean(is_indexed=True, is_stored=True))
register_field('has_reduction', Boolean(is_indexed=True))
register_field('is_buyable', Boolean(is_indexed=True))
register_field('ctime', DateTime(is_stored=True, is_indexed=True))
# XXX xapian can't sort decimal
register_field('stored_price', Integer(is_indexed=False, is_stored=True))

# Register resources
register_resource_class(Product)
register_resource_class(Products)
