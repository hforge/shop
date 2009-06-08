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
from itools.core import get_abspath, merge_dicts
from itools.csv import Table as BaseTable, CSVFile
from itools.datatypes import Decimal, String
from itools.gettext import MSG
from itools.stl import stl
from itools import vfs
from itools.xapian import PhraseQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import SelectWidget, TextWidget, stl_namespaces
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.countries import CountriesEnumerate

# Import from shipping
from schema import delivery_schema
from shipping_way_views import ShippingWay_Configure


class ShippingPricesCSV(CSVFile):

    columns = ['countries', 'max-weight', 'price']

    schema = {'countries': String,
              'max-weight': Decimal,
              'price': Decimal}


class ShippingPricesTable(BaseTable):

    record_schema = {
      'countries': CountriesEnumerate(mandatory=True, multiple=True,
                                      is_indexed=True),
      'max-weight': Decimal(mandatory=True, is_indexed=True),
      'price': Decimal(mandatory=True),
      }



class ShippingPrices(Table):

    class_id = 'shipping-prices'
    class_title = MSG(u'Shipping Prices')
    class_handler = ShippingPricesTable

    class_views = ['view', 'add_record']

    form = [
        SelectWidget('countries', title=MSG(u'Countries')),
        TextWidget('max-weight', title=MSG(u'Max Weight (Kg)')),
        TextWidget('price', title=MSG(u'Price'))]



class ShippingWay(Folder):

    class_id = 'shipping'
    class_title = MSG(u'Shipping')
    class_views = ['view', 'configure', 'history', 'prices']

    img = 'ui/shop/images/shipping.png'

    # Views
    configure = ShippingWay_Configure()
    history = GoToSpecificDocument(specific_document='history',
                                  title=MSG(u'History'))
    prices = GoToSpecificDocument(specific_document='prices',
                                  title=MSG(u'Prices'))


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Image
        body = vfs.open(get_abspath(cls.img)).read()
        img = Image._make_resource(Image, folder,
                                   '%s/logo.png' % name, body=body,
                                   **{'state': 'public'})

        # Import CSV with prices
        ShippingPrices._make_resource(ShippingPrices, folder,
                                      '%s/prices' % name)
        if kw.has_key('csv'):
            table = ShippingPricesTable()
            csv = ShippingPricesCSV(kw['csv'])
            for row in csv.get_rows():
                table.add_record({'countries': row.get_value('countries').split('@'),
                                  'max-weight': row.get_value('max-weight'),
                                  'price': row.get_value('price')})
            folder.set_handler('%s/prices' % name, table)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(), delivery_schema)


    def get_price(self, country, purchase_price, purchase_weight):
        list_price_ok = {}
        prices = self.get_resource('prices').handler
        # Get corresponding weight in table of price
        query = PhraseQuery('countries', country)
        for record in prices.search(query):
            max_weight = prices.get_record_value(record, 'max-weight')
            if purchase_weight < max_weight:
                list_price_ok[max_weight] = record
        if not list_price_ok:
            return None
        record = list_price_ok[max(list_price_ok.keys())]
        return prices.get_record_value(record, 'price')


    def get_logo(self, context):
        logo = self.get_resource('logo.png', soft=True)
        if logo:
            uri = context.get_link(logo)
        else:
            uri = '/ui/icons/48x48/text.png'
        return '%s/;download' % uri


    def get_namespace(self, context):
        namespace = {'name': self.name,
                     'description': self.get_property('description'),
                     'logo': self.get_logo(context),
                     'title': self.get_title()}
        return namespace



    html_form = list(XMLParser("""
        <form method="POST">
          <input type="hidden" name="shipping" value="${name}"/>
          <span stl:if="price">${price} €</span>
          <span stl:if="not price">Free</span>
          <input type="submit" id="button-order" value="Ok"/>
        </form>
        """,
        stl_namespaces))

    def get_widget_namespace(self, context, country, price, weight):
        price = self.get_price(country, price, weight)
        if price is None:
            return None
        ns = {'name': self.name,
              'price': price}
        html_form = stl(events=self.html_form, namespace=ns)
        ns = {'name': self.name,
              'img': self.get_logo(context),
              'title': self.get_title(),
              'price': price,
              'html_form': html_form}
        for key in ['description', 'enabled']:
            ns[key] = self.get_property(key)
        return ns


    def get_shipping_option(self, context):
        return None


    def get_namespace_shippings(self, context):
        namespace = []
        payments = self.get_resource('history')
        for record in payments.handler.get_records():
            kw = payments.get_record_namespace(context, record)
            kw['shipping_mode'] = self.get_title()
            namespace.append(kw)
        return namespace



register_resource_class(ShippingWay)
register_resource_class(ShippingPrices)
