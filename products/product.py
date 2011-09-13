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
from itools.datatypes import Integer, Decimal
from itools.gettext import MSG
from itools.uri import get_uri_name, resolve_uri2, get_reference
from itools.web import get_context
from itools.xml import TEXT, xml_to_text

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import XHTMLBody
from ikaaro.registry import register_resource_class, register_field
from ikaaro.workflow import WorkflowAware

# Import from itws
from itws.tags import TagsAware

# Import from shop
from declination import Declination, Declination_NewInstance
from dynamic_folder import DynamicFolder, DynamicProperty
from images import PhotoOrderedTable, ImagesFolder
from models import SpecificModelIs
from product_views import Product_NewProduct, Products_View, Product_ViewBox
from product_views import Product_CrossSellingViewBox
from product_views import Product_View, Product_Edit, Product_AddLinkFile
from product_views import Product_Delete
from product_views import Product_Print, Product_SendToFriend
from product_views import Product_DeclinationsView
from product_views import Product_ChangeProductModel, Products_Stock
from schema import product_schema
from taxes import TaxesEnumerate
from shop.cart import ProductCart
from shop.datatypes import IntegerRange
from shop.enumerate_table import EnumerateTable_to_Enumerate
from shop.enumerate_table import Restricted_EnumerateTable_to_Enumerate
from shop.folder import ShopFolder
from shop.manufacturers import ManufacturersEnumerate
from shop.modules import ModuleLoader
from shop.shop_views import Shop_Login, Shop_Register
from shop.utils import get_shop, get_group_name, format_price, generate_barcode
from shop.utils import CurrentFolder_AddImage, MiniTitle, get_product_filters


mail_stock_subject_template = MSG(u'Product out of stock')

mail_stock_body_template = MSG(u"""Hi,
The product {product_title} is out of stock\n
  {product_uri}\n
""")

class ConfigurationProperty(dict):

    resource = None
    context = None

    def __getitem__(self, key):
        shop = get_shop(self.resource)
        if key == 'show_ht_price':
            return shop.show_ht_price(self.context)
        raise ValueError, 'unknow configuration property'


class Product(WorkflowAware, TagsAware, DynamicFolder):

    class_id = 'product'
    class_title = MSG(u'Product')
    class_description = MSG(u'A product')
    class_version = '20100812'

    ##################
    # Configuration
    ##################
    viewbox = Product_ViewBox()
    viewbox_cls = Product_ViewBox
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
    declinations = Product_DeclinationsView()
    new_declination = Declination_NewInstance()
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
    add_image = CurrentFolder_AddImage()



    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(DynamicFolder.get_metadata_schema(),
                           WorkflowAware.get_metadata_schema(),
                           product_schema,
                           data=XHTMLBody(multilingual=True))


    @staticmethod
    def _make_resource(cls, folder, name, ctime=None, *args, **kw):
        from shop.cross_selling import CrossSellingTable
        if ctime is None:
            ctime = datetime.now()
        DynamicFolder._make_resource(cls, folder, name, ctime=ctime, *args,
                                     **kw)
        # Images folder
        ImagesFolder._make_resource(ImagesFolder, folder,
                                    '%s/images' % name, body='',
                                    title={'en': u'Images'})
        # Order images table
        PhotoOrderedTable._make_resource(PhotoOrderedTable, folder,
                                         '%s/order-photos' % name,
                                         title={'en': u'Order photos'})
        # Cross Selling table
        CrossSellingTable._make_resource(CrossSellingTable, folder,
                                         '%s/cross-selling' % name,
                                         title={'en': u'Cross selling'})


    def _get_dynamic_catalog_values(self):
        values = {}
        dynamic_schema = self.get_dynamic_schema()
        for key, datatype in get_product_filters().items():
            register_key = 'DFT-%s' % key
            if key in dynamic_schema:
                value = self.get_dynamic_property(key, dynamic_schema)
                if value and getattr(datatype, 'is_range', False):
                    value = int(value * 100)
                if value:
                    values[register_key] = value
        return values
        # XXX We have to refactor dynamic indexation
        # Import from ikaaro
        # from ikaaro.registry import get_register_fields
        #values = ShopFolder._get_catalog_values(self)
        #register_fields = get_register_fields()
        #model = self.get_product_model()
        #if model is None:
        #    return {}
        #for key, datatype in self.get_dynamic_schema().items():
        #    # We index dynamic properties that correspond to
        #    # an EnumerateTable datatype.
        #    # So we are able to know if enumerate value is used or not
        #    if issubclass(datatype, EnumerateTable_to_Enumerate) is True:
        #        register_key = 'DFT-%s' % datatype.enumerate_name
        #        if register_key not in register_fields:
        #            register_field(register_key, String(is_indexed=True))
        #        if datatype.multiple is True:
        #            values[register_key] = ' '.join(self.get_property(key))
        #        else:
        #            values[register_key] = self.get_property(key)
        ## Index declinations
        #declinations = list(self.search_resources(cls=Declination))
        #for key in model.get_property('declinations_enumerates'):
        #    declinations_values = set()
        #    for declination in declinations:
        #        value = declination.get_property(key)
        #        if isinstance(value, list):
        #            declinations_values.union(value)
        #        else:
        #            declinations_values.add(value)
        #    register_key = 'DFT-%s' % key
        #    if register_key not in register_fields:
        #        register_field(register_key, String(is_indexed=True, multiple=True))
        #    if values.has_key(register_key):
        #        values[register_key] += declinations_values
        #    else:
        #        values[register_key] = declinations_values
        #return values


    def _get_preview_content(self, languages):
        # TagsAware preview not used for products
        # Saves half the time of reindexing!
        return None


    def _get_catalog_values(self):
        values = merge_dicts(DynamicFolder._get_catalog_values(self),
                             TagsAware._get_catalog_values(self),
                             self._get_dynamic_catalog_values())
        # Data
        data = self.get_property('data')
        if data is not None:
            data = xml_to_text(data)
        values['data'] = data
        # Reference
        values['reference'] = self.get_property('reference')
        # Manufacturer
        values['manufacturer'] = str(self.get_property('manufacturer'))
        # Supplier
        values['supplier'] = str(self.get_property('supplier'))
        # Stock quantity
        values['stock_quantity'] = self.get_property('stock-quantity')
        # Product models
        values['product_model'] = str(self.get_property('product_model'))
        # Images
        order = self.get_resource('order-photos')
        ordered_names = list(order.get_ordered_names())
        values['has_images'] = (len(ordered_names) != 0)
        # Price # XXX We can't sort decimal, so transform to int
        values['stored_price'] = int(self.get_price_with_tax() * 100)
        values['stored_weight'] = int(self.get_weight() * 100)
        # Price
        values['ht_price'] = self.get_price_without_tax()
        values['ttc_price'] = self.get_price_with_tax()
        # Creation time
        values['ctime'] = self.get_property('ctime')
        # Publication date
        values['pub_datetime'] = self.get_property('pub_datetime')
        # Promotion
        values['has_reduction'] = self.get_property('has_reduction')
        # not_buyable_by_groups
        values['not_buyable_by_groups'] = self.get_property('not_buyable_by_groups')
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
        return self.get_resource(product_model)


    def to_text(self):
        result = {}
        languages = self.get_site_root().get_property('website_languages')
        product_model = self.get_product_model()
        schema = {}
        if product_model:
            schema = product_model.get_model_schema()
        purchase_options_schema = self.get_purchase_options_schema()
        declinations = list(self.search_resources(cls=Declination))

        for language in languages:
            texts = result.setdefault(language, [])
            for key in ('title', 'description'):
                value = self.get_property(key, language=language)
                if value:
                    texts.append(value)
            # Parent category
            current_category = self.parent
            while current_category.class_id == 'category':
                texts.append(current_category.get_title(language=language))
                current_category = current_category.parent
            # data (html)
            events = self.get_property('data', language=language)
            if events:
                text = [ unicode(value, 'utf-8') for event, value, line in events
                         if event == TEXT ]
                if text:
                    texts.append(u' '.join(text))
            # Dynamic properties
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
        # Purchase options
        for declination in declinations:
            for key, datatype in purchase_options_schema.iteritems():
                name = declination.get_property(key)
                value = datatype.to_text(name, languages)
                if value:
                    texts.append(value)

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
        # XXX If handle_stock property is false manage_stock should be false
        manage_stock = self.get_stock_option() != 'accept'
        purchase_options_names = self.get_purchase_options_names()
        # Base product
        stock_quantity = self.get_property('stock-quantity')
        products = {}
        if len(declinations)==0:
            products['base_product'] = {
                'price_ht': format_price(self.get_price_without_tax()),
                'price_ttc': format_price(self.get_price_with_tax()),
                'weight': str(self.get_weight()),
                'image': [],
                'option': {},
                'is_default': True,
                'stock': stock_quantity if manage_stock else None}
        # Other products (declinations)
        for declination in declinations:
            dynamic_schema = declination.get_dynamic_schema()
            stock_quantity = declination.get_quantity_in_stock()
            price_ht = self.get_price_without_tax(id_declination=declination.name)
            price_ttc = self.get_price_with_tax(id_declination=declination.name)
            image = None#declination.get_property('associated-image')
            products[declination.name] = {
              'price_ht': format_price(price_ht),
              'price_ttc': format_price(price_ttc),
              'weight': str(declination.get_weight()),
              'image': get_uri_name(image) if image else None,
              'is_default': declination.get_property('is_default'),
              'option': {},
              'stock': stock_quantity if manage_stock else None}
            for name in purchase_options_names:
                value = declination.get_dynamic_property(name, dynamic_schema)
                if value:
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
            dynamic_schema = declination.get_dynamic_schema()
            for name in purchase_options_names:
                value = declination.get_dynamic_property(name, dynamic_schema)
                if not value:
                    continue
                if not values.has_key(name):
                    values[name] = set([])
                values[name].add(value)
        # Build datatype / widget
        enumerates_folder = shop.get_resource('enumerates')
        for name in purchase_options_names:
            if values.get(name) is None or len(values[name]) == 0:
                continue
            enumerate_table = enumerates_folder.get_resource(name)
            datatype = Restricted_EnumerateTable_to_Enumerate(
                          enumerate_name=name, values=values[name])
            widget_cls = enumerate_table.widget_cls
            widget = widget_cls(name, has_empty_option=False)
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
            dynamic_schema = declination.get_dynamic_schema()
            value = [kw.get(x) ==
                  (declination.get_dynamic_property(x, dynamic_schema) or None)
                        for x in purchase_options_schema]
            if set(value) == set([True]):
                return declination.name
        return None


    def get_declination_namespace(self, declination_name):
        namespace = []
        shop = get_shop(self)
        declination = self.get_resource(declination_name)
        dynamic_schema = declination.get_dynamic_schema()
        enumerates_folder = shop.get_resource('enumerates')
        for name in self.get_purchase_options_names():
            value = declination.get_dynamic_property(name, dynamic_schema)
            if not value:
                continue
            enumerate_table = enumerates_folder.get_resource(name)
            datatype = EnumerateTable_to_Enumerate(enumerate_name=name)
            namespace.append({'title': enumerate_table.get_title(),
                              'value': datatype.get_value(value)})
        return namespace


    # XXX We should be able to activate it or not
    #def get_available_languages(self, languages):
    #    from itws.utils import is_empty
    #    available_langs = []
    #    for language in languages:
    #        events = self.get_property('data', language=language)
    #        title = self.get_property('title', language=language)
    #        if events and is_empty(events) is False and len(title.strip()):
    #            available_langs.append(language)
    #    return available_langs


    ##################################################
    ## Namespace
    ##################################################
    def get_small_namespace(self, context):
        title = self.get_property('title')
        # Specific model is ?
        specific_model_is = SpecificModelIs()
        product_model = self.get_product_model()
        if product_model:
            product_model_name = product_model.name
        else:
            product_model_name = None
        specific_model_is.model_name = product_model_name
        # Dynamic property
        dynamic_property = DynamicProperty()
        dynamic_property.resource = self
        dynamic_property.context = context
        dynamic_property.schema = self.get_dynamic_schema()
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
        # Minititle
        mini_title = MiniTitle()
        mini_title.context = context
        mini_title.here = self
        # Return namespace
        return {
          'name': self.name,
          'lang': lang,
          'module': shop_module,
          'specific_model_is': specific_model_is,
          'dynamic_property': dynamic_property,
          'category': category,
          'cover': self.get_cover_namespace(context),
          'description': self.get_property('description'),
          'href': context.get_link(self),
          'manufacturer': ManufacturersEnumerate.get_value(self.get_property('manufacturer')),
          'mini-title': mini_title,
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
        table = self.get_resource('cross-selling', soft=True)
        if table is None:
            # If table do not exist we use default cross selling
            shop = get_shop(self)
            table = shop.get_resource('cross-selling')
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
        namespace = {'name': self.name,
                     'abspath': self.get_abspath(),
                     'price': self.get_price_namespace()}
        # Get basic informations
        namespace['href'] = context.get_link(self)
        for key in product_schema.keys():
            if key=='data':
                continue
            namespace[key] = self.get_property(key)
        # Category
        namespace['category'] = {
            'name': self.parent.name,
            'href': context.get_link(self.parent),
            'breadcrumb_title': self.parent.get_property('breadcrumb_title'),
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
        namespace['data'] = self.get_property('data')
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
        namespace['is_buyable'] = self.is_buyable(context)
        # Cross selling
        namespace['cross_selling'] = self.get_cross_selling_namespace(context)
        # Authentificated ?
        ac = self.get_access_control()
        namespace['is_authenticated'] = ac.is_authenticated(context.user, self)
        # Configuration
        configuration = ConfigurationProperty()
        configuration.context = context
        configuration.resource = self
        namespace['configuration'] = configuration
        # Shop modules
        shop_module = ModuleLoader()
        shop_module.context = context
        shop_module.here = self
        namespace['module'] = shop_module
        return namespace


    #####################
    # Images
    #####################
    def get_preview_thumbnail(self):
        container = self
        cover = self.get_property('cover')
        # If no cover get default one
        if not cover:
            container = self.parent
            cover = container.get_property('default_product_cover')
        # If no cover we return None
        if not cover:
            return None
        return container.get_resource(cover, soft=True)


    def get_cover_namespace(self, context):
        image = self.get_preview_thumbnail()
        if not image:
            return
        return {'href': context.get_link(image),
                'name': image.name,
                'key': image.handler.key,
                'title': image.get_property('title') or self.get_title()}


    def get_images_namespace(self, context):
        images = []
        for image in self.get_ordered_photos(context):
            images.append({'name': image.name,
                           'href': context.get_link(image),
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
    def is_buyable(self, context, quantity=1):
        shop = get_shop(self)
        group_name = get_group_name(shop, context)
        return (self.get_price_without_tax() != decimal(0) and
                group_name not in self.get_property('not_buyable_by_groups') and
                self.get_statename() == 'public')


    def get_reference(self, id_declination=None):
        if id_declination:
            declination = self.get_resource(id_declination, soft=True)
            if declination:
                reference = declination.get_property('reference')
                if reference:
                    return reference
        return self.get_property('reference')


    def get_price_prefix(self):
        shop = get_shop(self)
        context = get_context()
        group_name = get_group_name(shop, context)
        if get_uri_name(group_name) == 'pro':
            return 'pro-'
        return ''


    def get_tax_value(self, prefix=None):
        shop = get_shop(self)
        if prefix is None:
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
                               with_reduction=True, pretty=False, prefix=None):
        if prefix is None:
            prefix = self.get_price_prefix()
        # Base price
        if with_reduction is True and self.get_property('%shas_reduction' % prefix):
            price = self.get_property('%sreduce-pre-tax-price' % prefix)
        else:
            price = self.get_property('%spre-tax-price' % prefix)
        # Declination
        if id_declination:
            declination = self.get_resource(id_declination)
            price = price + declination.get_price_impact(prefix)
        # Format price
        if pretty is True:
            return format_price(price)
        return price


    def get_price_with_tax(self, id_declination=None,
                            with_reduction=True, pretty=False, prefix=None):
        price = self.get_price_without_tax(id_declination,
                    with_reduction=with_reduction, prefix=prefix)
        price = price * self.get_tax_value(prefix=prefix)
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

    #######################
    ## Computed fields
    #######################
    computed_schema = {'frontoffice_uri': String(title=MSG(u'Frontoffice link')),
                       'cover_uri': String(title=MSG(u'Cover link')),
                       'price_with_tax': Decimal(title=MSG(u'Price with tax'))}

    @property
    def price_with_tax(self):
        return self.get_price_with_tax(with_reduction=True)


    @property
    def frontoffice_uri(self):
        shop = get_shop(self)
        site_root = shop.get_site_root()
        base_uri = shop.get_property('shop_uri')
        end_uri = site_root.get_pathto(self)
        return str(get_reference(base_uri).resolve(end_uri))


    @property
    def cover_uri(self):
        shop = get_shop(self)
        site_root = shop.get_site_root()
        cover = self.get_preview_thumbnail()
        if not cover:
            return None
        base_uri = shop.get_property('shop_uri')
        end_uri = site_root.get_pathto(cover)
        return str('%s/;download' % get_reference(base_uri).resolve(end_uri))


    #######################
    ## Class views
    #######################
    default_class_views = ['declinations', 'new_declination', 'images',
                   'order', 'edit_cross_selling', 'delete_product', 'commit_log']

    @property
    def class_views(self):
        context = get_context()
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return ['edit'] + self.default_class_views
        return ['view', 'edit'] + self.default_class_views


    def get_links(self):
        return DynamicFolder.get_links(self)


    def update_links(self, source, target):
        return DynamicFolder.update_links(self, source, target)


    def update_relative_links(self, source):
        return DynamicFolder.update_relative_links(self, source)


    def update_20110311(self):
        # Remove old attributes
        for key in ['is_buyable', 'reduction', 'categories']:
            self.del_property(key)



class Products(ShopFolder):

    class_id = 'products'
    class_title = MSG(u'Products')
    class_views = ['browse_content', 'new_product']
    class_version = '20100229'

    # Views
    browse_content = Products_View()
    stock = Products_Stock()
    new_product = Product_NewProduct()

    def can_paste(self, source):
        return isinstance(source, Product)


    def get_document_types(self):
        return []



# Register fields
register_field('reference', String(is_indexed=True, is_stored=True))
register_field('stock_quantity', Integer(is_indexed=True, is_stored=True))
register_field('manufacturer', String(is_indexed=True))
register_field('supplier', String(is_indexed=True, multiple=True))
register_field('product_model', String(is_indexed=True, is_stored=True))
register_field('has_images', Boolean(is_indexed=True, is_stored=True))
register_field('has_reduction', Boolean(is_indexed=True))
register_field('not_buyable_by_groups', String(is_indexed=True, multiple=True))
register_field('ctime', DateTime(is_stored=True, is_indexed=True))
register_field('data', Unicode(is_indexed=True))
register_field('ht_price', Decimal(is_indexed=True, is_stored=True))
register_field('ttc_price', Decimal(is_indexed=True, is_stored=True))
# XXX xapian can't sort decimal
register_field('stored_price', Integer(is_indexed=False, is_stored=True))
register_field('stored_weight', Integer(is_indexed=False, is_stored=True))

# Register resources
register_resource_class(Product)
register_resource_class(Products)
