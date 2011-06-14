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

# Import from itools
from itools.datatypes import Email, Unicode, Boolean, Integer, String
from itools.gettext import MSG
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.registry import register_resource_class
from ikaaro.webpage import WebPage

# Import from project
from enumerates import Devises
from enumerate_table import EnumeratesFolder
from addresses import Addresses
from categories import Category
from countries import Countries, CountriesZones
from cross_selling import CrossSellingTable
from datatypes import ImagePathDataType
from editorial import Shop_EditorialView
from enumerates import BarcodesFormat, SortBy_Enumerate, CountriesZonesEnumerate
from folder import ShopFolder
from modules import Modules
from orders import Orders
from products import Product, ProductModels
from products.taxes import Taxes_TableResource, Taxes_TableHandler
from shipping import Shippings
from shop_payments import ShopPayments
from shop_views import Shop_Addresses, Shop_AddressesBook, Shop_Login
from shop_views import Shop_Delivery, Shop_ViewCart, Shop_Configure
from shop_views import Shop_RegisterProgress, Shop_AddAddressProgress
from shop_views import Shop_ShowRecapitulatif, Shop_EditAddressProgress
from shop_views import Shop_GetProductStock, Shop_Configuration
from shop_views import Shop_Administration
from suppliers import Suppliers, Supplier
from user import ShopUser, Customers
from user_group import ShopUser_Groups


catalog_is_initialize = False


class Shop(ShopFolder):

    class_id = 'shop'
    class_title = MSG(u'Shop')
    class_views = ['view_cart']
    class_version = '20100622'

    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['addresses',
                          'categories', 'customers', 'groups',
                          'orders', 'payments',
                          'products', 'products-models',
                          'shippings', 'countries',
                          'terms-and-conditions-of-use', 'taxes']


    ###############################
    # Classes to override
    # for specific needs
    ###############################
    product_class = Product
    category_class = Category
    payments_class = ShopPayments
    supplier_class = Supplier
    user_class = ShopUser

    ####################################
    ## Views
    ####################################

    login = Shop_Login()

    # Administrator shop views
    administration = Shop_Administration()
    configuration = Shop_Configuration()
    get_product_stock = Shop_GetProductStock()
    configure = Shop_Configure()
    editorial = Shop_EditorialView()

    #------------------------------
    # 6 Steps for payment process
    #------------------------------

    # 1) View cart
    view_cart = Shop_ViewCart()

    # 2) Login/Register
    register = Shop_RegisterProgress()

    # 3) Choose/edit/add addresses
    addresses = Shop_Addresses()
    addresses_book = Shop_AddressesBook()
    edit_address = Shop_EditAddressProgress()
    add_address = Shop_AddAddressProgress()

    # 4) Choose delivery
    delivery = Shop_Delivery()

    # 5) Recapitulatif / payment
    show_recapitulatif = Shop_ShowRecapitulatif()

    # 6) Payment end (Define in payments views)

    #def __init__(self, metadata):
    #from catalog import register_dynamic_fields
    #    # Super
    #    super(Shop, self).__init__(metadata)
    #    # XXX Hack
    #    # Register dynamic catalog fields
    #    global catalog_is_initialize
    #    if catalog_is_initialize is False:
    #        catalog_is_initialize = True
    #        register_dynamic_fields(get_context())
    #        modules = self.get_resource('shop/modules')


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        root = ShopFolder._make_resource(cls, folder, name, **kw)
        # Payments module
        cls.payments_class._make_resource(cls.payments_class, folder,
                                '%s/payments' % name,
                                title={'en': u'Payment module'})
        # Modules
        Modules._make_resource(Modules, folder,
                      '%s/modules' % name, title={'en': u'Modules'})
        # Suppliers
        Suppliers._make_resource(Suppliers, folder,
                      '%s/suppliers' % name, title={'en': u'Suppliers'})
        # Customers
        Customers._make_resource(Customers, folder,
                      '%s/customers' % name, title={'en': u'Customers'})
        # Product Models
        ProductModels._make_resource(ProductModels, folder, '%s/products-models' % name,
                                    title={'en': u'Product Models'})
        # Orders
        Orders._make_resource(Orders, folder, '%s/orders' % name,
                              title={'en': u'Orders'})
        # ShopUser_Groups
        ShopUser_Groups._make_resource(ShopUser_Groups, folder, '%s/groups' % name,
                                        title={'en': u'User groups'})
        # Addresses
        Addresses._make_resource(Addresses, folder, '%s/addresses' % name,
                                 title={'en': u'Addresses'})
        # Countries
        Countries._make_resource(Countries, folder, '%s/countries' % name,
                                 title={'en': u'countries'})
        # Countries zone
        CountriesZones._make_resource(CountriesZones, folder,
                '%s/countries-zones' % name, title={'en': u'Countries Zones'})
        # EnumeratesFolder
        EnumeratesFolder._make_resource(EnumeratesFolder, folder,
                                    '%s/enumerates' % name, title={'en': u'Enumerates'})
        # Shipping
        Shippings._make_resource(Shippings, folder, '%s/shippings' % name,
                                 title={'en': u'Shipping'})
        # Conditions of users
        WebPage._make_resource(WebPage, folder, '%s/terms-and-conditions-of-use' % name,
                                **{'title': {'fr': u'Conditions Générales de ventes',
                                             'en': u'Terms and conditions of user'},
                                   'state': 'public'})
        # Default cross Selling configuration
        CrossSellingTable._make_resource(CrossSellingTable, folder,
                                         '%s/cross-selling' % name,
                                         title={'en': u'Cross selling'})
        # Taxes
        Taxes_TableResource._make_resource(Taxes_TableResource, folder, '%s/taxes' % name,
                                **{'title': {'fr': u'TVA',
                                             'en': u'Taxes'}})
        table = Taxes_TableHandler()
        table.add_record({'value': '19.6'})
        folder.set_handler('%s/taxes' % name, table)




    @classmethod
    def get_metadata_schema(cls):
        schema = ShopFolder.get_metadata_schema()
        schema['shop_uri'] = String
        schema['shop_backoffice_uri'] = String
        schema['order_notification_mails'] = Email(multiple=True)
        schema['shop_default_zone'] = CountriesZonesEnumerate(default=0)
        schema['shop_sort_by'] = SortBy_Enumerate
        schema['shop_sort_reverse'] = Boolean
        schema['categories_batch_size'] = Integer(default=20)
        schema['devise'] = Devises(default='978')
        schema['bill_logo'] = ImagePathDataType
        schema['pdf_signature'] = Unicode
        schema['barcode_format'] = BarcodesFormat
        schema['show_sub_categories'] = Boolean
        schema['hide_not_buyable_products'] = Boolean
        schema['product_cover_is_mandatory'] = Boolean
        schema['log_authentification'] = Boolean
        schema['registration_need_email_validation'] = Boolean
        return schema


    def get_document_types(self):
        return []

    ##############################
    # API
    ##############################

    def get_pdf_logo_key(self, context):
        logo = self.get_property('bill_logo')
        resource_logo = self.get_resource(logo, soft=True) if logo else None
        if resource_logo is not None:
            key = resource_logo.handler.key
            return context.database.fs.get_absolute_path(key)
        return None

    ##############################
    # XXX To deplace
    ##############################
    def get_user_main_address(self, user_name):
        # TODO: user can define his default address
        addresses = self.get_resource('addresses').handler
        for record in addresses.search(user=str(user_name)):
            return record
        return None


    def get_user_address_namespace(self, id):
        addresses = self.get_resource('addresses').handler
        return addresses.get_record_namespace(id)

    ##############################
    # Configuration
    ##############################
    def show_ht_price(self, context):
        if context.user:
            group = context.user.get_group(context)
            return group.get_property('show_ht_price')
        return False


    def has_pro_price(self):
        # XXX Improve in future
        root = self.get_root()
        query = [PhraseQuery('format', 'user-group'),
                 PhraseQuery('name', 'pro')]
        search = root.search(AndQuery(*query))
        return len(search) > 0


register_resource_class(Shop)
