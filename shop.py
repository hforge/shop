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

# Import from ikaaro
from ikaaro.registry import register_resource_class
from ikaaro.webpage import WebPage

# Import from project
from enumerate_table import EnumeratesFolder
from addresses import Addresses
from categories import Category
from countries import Countries, CountriesZones
from cross_selling import CrossSellingTable
from datatypes import ImagePathDataType
from editorial import Shop_EditorialView
from enumerates import BarcodesFormat, SortBy_Enumerate, CountriesZonesEnumerate
from manufacturers import Manufacturers, Manufacturer
from modules import Modules
from orders import Orders
from products import Products, Product, ProductModels
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
from utils import ShopFolder


class Shop(ShopFolder):

    class_id = 'shop'
    class_title = MSG(u'Shop')
    class_views = ['view_cart']
    class_version = '20100607'

    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['addresses',
                          'categories', 'customers', 'groups',
                          'manufacturers', 'orders', 'payments',
                          'products', 'products-models',
                          'shippings', 'countries',
                          'terms-and-conditions-of-use', 'taxes']

    ####################################
    # Shop configuration
    ####################################

    # Mail
    mail_template = '/ui/shop/mail.xhtml'

    # Reduce string (for product mini-title)
    product_title_word_treshold = 50
    product_title_phrase_treshold= 150

    # Pro price
    has_pro_price = False

    # XXX
    profile_items = []

    ###############################
    # Classes to override
    # for specific needs
    ###############################
    manufacturer_class = Manufacturer
    product_class = Product
    category_class = Category
    payments_class = ShopPayments
    supplier_class = Supplier
    user_class = ShopUser
    user_groups_class = []

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


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        root = ShopFolder._make_resource(cls, folder, name, **kw)
        # Payments module
        cls.payments_class._make_resource(cls.payments_class, folder,
                                '%s/payments' % name,
                                title={'en': u'Payment module'})
        # Manufacturers
        Manufacturers._make_resource(Manufacturers, folder,
                      '%s/manufacturers' % name, title={'en': u'Manufacturers'})
        # Modules
        Modules._make_resource(Modules, folder,
                      '%s/modules' % name, title={'en': u'Modules'})
        # Suppliers
        Suppliers._make_resource(Suppliers, folder,
                      '%s/suppliers' % name, title={'en': u'Suppliers'})
        # Products
        Products._make_resource(Products, folder, '%s/products' % name,
                                title={'en': u'Products'})
        # Product Models
        ProductModels._make_resource(ProductModels, folder, '%s/products-models' % name,
                                    title={'en': u'Product Models'})
        # Orders
        Orders._make_resource(Orders, folder, '%s/orders' % name,
                              title={'en': u'Orders'})
        # Customers
        Customers._make_resource(Customers, folder, '%s/customers' % name,
                                 title={'en': u'Customers'})
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
        schema['bill_logo'] = ImagePathDataType
        schema['pdf_signature'] = Unicode
        schema['barcode_format'] = BarcodesFormat
        schema['show_sub_categories'] = Boolean
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
        ns_addresses = []
        addresses = self.get_resource('addresses').handler
        for record in addresses.search(user=str(user_name)):
            return record
        return None


    def get_user_address_namespace(self, id):
        addresses = self.get_resource('addresses').handler
        return addresses.get_record_namespace(id)


    def update_20090819(self):
        if self.get_resource('enumerates', soft=True) is not None:
            return
        EnumeratesFolder.make_resource(EnumeratesFolder, self, 'enumerates')


    def update_20090825(self):
        if self.get_resource('cross-selling', soft=True) is not None:
            return
        CrossSellingTable.make_resource(CrossSellingTable, self,
                              'cross-selling', title={'en': u'Cross selling'})


    def update_20090910(self):
        """ Add zones to countries
        """
        from itools.csv import CSVFile, Property
        from itools.core import get_abspath
        if self.get_resource('countries-zones', soft=True) is not None:
            return
        CountriesZones.make_resource(CountriesZones, self,
                          'countries-zones', title={'en': u'Countries Zones'})
        # Get list of countries
        countries = []
        handler = self.get_resource('countries').handler
        for record in handler.get_records():
            countries.append(handler.get_record_value(record, 'title'))
        # Do update
        zones = []
        csv = CSVFile(get_abspath('data/countries.csv'))
        for line in csv.get_rows():
            country = unicode(line[0], 'utf-8')
            zone = unicode(line[1], 'utf-8')
            if zone not in zones:
                zones.append(zone)
            if country in countries:
                # Update zone
                for record in handler.get_records():
                    if handler.get_record_value(record, 'title') == country:
                          handler.update_record(record.id,
                                **{'zone': str(zones.index(zone))})
            else:
                # Add new country
                handler.add_record({'title': Property(country, language='fr'),
                                    'zone': str(zones.index(zone)),
                                    'enabled': True})

    def update_20091008(self):
        if self.get_resource('customers', soft=True) is not None:
            return
        Customers.make_resource(Customers, self, 'customers')


    def update_20091009(self):
        if self.get_resource('manufacturers', soft=True) is not None:
            return
        Manufacturers.make_resource(Manufacturers, self, 'manufacturers')


    def update_20091110(self):
        if self.get_resource('suppliers', soft=True) is not None:
            return
        Suppliers.make_resource(Suppliers, self, 'suppliers')


    def update_20091201(self):
        self.del_property('activate_mail_html')
        self.del_property('shop_signature')
        self.del_property('shop_from_addr')


    def update_20100412(self):
        if self.get_resource('modules', soft=True) is not None:
            return
        Modules.make_resource(Modules, self, 'modules')


    def update_20100607(self):
        if self.get_resource('groups', soft=True) is not None:
            return
        ShopUser_Groups.make_resource(ShopUser_Groups, self, 'groups')


register_resource_class(Shop)
