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

# Import from itools
from itools import vfs
from itools.core import get_abspath, merge_dicts
from itools.csv import Table as BaseTable, CSVFile
from itools.datatypes import Decimal, Enumerate, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.stl import stl
from itools.web import get_context
from itools.xapian import PhraseQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import SelectWidget, TextWidget, stl_namespaces
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.countries import CountriesZonesEnumerate
from shop.utils import get_shop, ShopFolder

# Import from shipping
from enumerates import ShippingStates
from schema import delivery_schema
from shipping_way_views import ShippingWay_Configure, ShippingWay_RecordAdd
from shipping_way_views import ShippingWay_RecordEdit, ShippingWay_RecordView


class ShippingWayBaseTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, is_indexed=True),
        'state': ShippingStates,
        'price': Decimal,
        'weight': Decimal,
        'number': String,
        'description': Unicode}



class ShippingWayTable(Table):

    class_id = 'shipping-way-table'
    class_handler = ShippingWayBaseTable

    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        SelectWidget('state', title=MSG(u'State')),
        TextWidget('price', title=MSG(u'Price')),
        TextWidget('weight', title=MSG(u'Weight')),
        TextWidget('number', title=MSG(u'Numéro')),
        TextWidget('description', title=MSG(u'Description')),
        ]

    def get_record_namespace(self, context, record):
        namespace = {}
        # Id
        namespace['id'] = record.id
        namespace['shipping_mode'] = self.parent.get_title()
        # Complete id
        namespace['complete_id'] = '%s-%s' % (self.parent.name, record.id)
        # Base namespace
        for key in self.handler.record_schema.keys():
            namespace[key] = self.handler.get_record_value(record, key)
        # State
        namespace['state'] = ShippingStates.get_value(namespace['state'])
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        namespace['ts'] = format_datetime(value,  accept)
        return namespace


class ShippingPricesCSV(CSVFile):

    columns = ['zone', 'max-weight', 'price']

    schema = {'zone': Unicode,
              'max-weight': Decimal,
              'price': Decimal}


class ShippingPricesTable(BaseTable):

    record_schema = {
      'zone': CountriesZonesEnumerate(mandatory=True, is_indexed=True),
      'max-weight': Decimal(mandatory=True, is_indexed=True),
      'price': Decimal(mandatory=True)}



class ShippingPrices(Table):

    class_id = 'shipping-prices'
    class_title = MSG(u'Shipping Prices')
    class_handler = ShippingPricesTable

    class_views = ['view', 'add_record']

    form = [
        SelectWidget('zone', title=MSG(u'Zone')),
        TextWidget('max-weight', title=MSG(u'Max Weight (Kg)')),
        TextWidget('price', title=MSG(u'Price'))]



class ShippingWay(ShopFolder):

    class_id = 'shipping'
    class_title = MSG(u'Shipping')
    class_description = MSG(u'Allow to define your own shipping way')
    class_views = ['view', 'configure', 'history', 'prices']
    class_version = '20090918'

    img = '../ui/shop/images/shipping.png'


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        # Image
        body = vfs.open(get_abspath(cls.img)).read()
        img = Image._make_resource(Image, folder,
                                   '%s/logo.png' % name, body=body,
                                   **{'state': 'public'})
        # Load zones
        shop = get_context().resource.parent
        zones = []
        handler = shop.get_resource('countries-zones').handler
        for record in handler.get_records():
            zones.append(handler.get_record_value(record, 'title'))
        # Import CSV with prices
        ShippingPrices._make_resource(ShippingPrices, folder,
                                      '%s/prices' % name)
        if getattr(cls, 'csv', None):
            table = ShippingPricesTable()
            csv = ShippingPricesCSV(get_abspath(cls.csv))
            for row in csv.get_rows():
                table.add_record(
                  {'zone': str(zones.index(row.get_value('zone'))),
                   'max-weight': row.get_value('max-weight'),
                   'price': row.get_value('price')})
            folder.set_handler('%s/prices' % name, table)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(), delivery_schema)


    def get_price(self, country, purchase_weight):
        shop = get_shop(self)
        # Is Free ?
        if self.get_property('is_free'):
            return decimal(0)
        # Transform country to zone
        countries = shop.get_resource('countries').handler
        country_record = countries.get_record(int(country))
        zone = countries.get_record_value(country_record, 'zone')
        # Calcul price
        list_price_ok = {}
        prices = self.get_resource('prices').handler
        # Get corresponding weight in table of price
        for record in prices.search(PhraseQuery('zone', zone)):
            max_weight = prices.get_record_value(record, 'max-weight')
            price = prices.get_record_value(record, 'price')
            if purchase_weight < max_weight:
                list_price_ok[max_weight] = record
        # No price, we return None
        if not list_price_ok:
            return None
        record = list_price_ok[min(list_price_ok.keys())]
        return prices.get_record_value(record, 'price')


    def get_logo(self, context):
        logo = self.get_property('logo')
        resource = self.get_resource(logo, soft=True)
        if resource is None:
            return
        return '%s/;download' % context.get_link(resource)


    def get_shipping_option(self, context):
        return None


    def get_namespace(self, context):
        language = self.get_content_language(context)
        return  {'name': self.name,
                 'description': self.get_property('description', language),
                 'logo': self.get_logo(context),
                 'title': self.get_title(language)}


    html_form = list(XMLParser("""
        <form method="POST">
          <input type="hidden" name="shipping" value="${name}"/>
          <span stl:if="price">${price} €</span>
          <span stl:if="not price">Free</span>
          <input type="submit" id="button-order" value="Ok"/>
        </form>
        """,
        stl_namespaces))

    def get_widget_namespace(self, context, country, weight):
        price = self.get_price(country, weight)
        if price is None:
            return None
        ns = {'name': self.name,
              'price': price}
        html_form = stl(events=self.html_form, namespace=ns)
        language = self.get_content_language(context)
        ns = {'name': self.name,
              'img': self.get_logo(context),
              'title': self.get_title(language),
              'price': price,
              'html_form': html_form}
        for key in ['description', 'enabled']:
            ns[key] = self.get_property(key, language)
        return ns


    def update_20090918(self):
        self.set_property('logo', 'logo.png')


    # Views
    configure = ShippingWay_Configure()
    history = GoToSpecificDocument(specific_document='history',
                                  title=MSG(u'History'))
    prices = GoToSpecificDocument(specific_document='prices',
                                  title=MSG(u'Prices'))

    # Backoffice order views
    order_view = ShippingWay_RecordView()
    order_add_view = ShippingWay_RecordAdd()
    order_edit_view = ShippingWay_RecordEdit()



class ShippingWaysEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        context = get_context()
        shop = get_shop(context.resource)
        shippings = shop.get_resource('shippings')
        for way in shippings.search_resources(cls=ShippingWay):
            options.append({'name': way.name,
                            'value': way.get_title(),
                            'enabled': way.get_property('enabled')})
        return options


register_resource_class(ShippingWay)
register_resource_class(ShippingWayTable)
register_resource_class(ShippingPrices)
