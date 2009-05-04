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
from itools import vfs, get_abspath
from itools.csv import Table as BaseTable, CSVFile
from itools.datatypes import Decimal, String
from itools.gettext import MSG
from itools.handlers import merge_dicts
from itools.stl import stl
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
from countries import CountriesEnumerate
from schema import delivery_schema
from shipping_views import ShippingsView, Shipping_View, Shipping_Configure


class ShippingPricesCSV(CSVFile):

    columns = ['countries', 'max-weight', 'price']

    schema = {'countries': String,
              'max-weight': Decimal,
              'price': Decimal}


class ShippingPricesTable(BaseTable):

    record_schema = {
      'countries': CountriesEnumerate(mandatory=True, multiple=True,
                                      index='keyword'),
      'max-weight': Decimal(mandatory=True, index='keyword'),
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



class Shipping(Folder):

    class_id = 'shipping'
    class_title = MSG(u'Shipping')
    class_views = ['view', 'configure', 'prices']

    img = 'ui/shop/images/shipping.png'

    # Views
    view = Shipping_View()
    configure = Shipping_Configure()
    prices = GoToSpecificDocument(specific_document='prices',
                                  title=MSG(u'Prices'))


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Image
        kw = {}
        kw['state'] = 'public'
        body = vfs.open(get_abspath(cls.img)).read()
        img = Image._make_resource(Image, folder,
                                   '%s/logo.png' % name, body=body, **kw)

        # Prices
        ShippingPrices._make_resource(ShippingPrices, folder,
                                      '%s/prices' % name)

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
        if self.has_resource('logo.png'):
            logo = self.get_resource('logo.png')
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
        if not price:
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



class Shippings(Folder):

    class_id = 'shippings'
    class_title = MSG(u'Shipping')
    class_views = ['view', 'new_resource?type=shipping']


    # Views
    view = ShippingsView()


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # XXX
        from shipping_modes import Collisimo, ShippShop
        # Init with some shippings mode
        for c in [Collisimo, ShippShop]:
            c._make_resource(c, folder, '%s/%s' % (name, c.class_id))



    def get_document_types(self):
        return [Shipping]


    def get_namespace_shipping_ways(self, context, country, price, weight):
        namespace = []
        for mode in self.search_resources(cls=Shipping):
            if not mode.get_property('enabled'):
                continue
            widget = mode.get_widget_namespace(context, country, price, weight)
            if widget:
                namespace.append(widget)
        # No price corresponding to options,
        # we should set a default price.
        return namespace


    def get_namespace_shipping_way(self, context, name, country, price, weight):
        shipping = self.get_resource(name)
        if not shipping.get_property('enabled'):
            return None
        return shipping.get_widget_namespace(context, country, price, weight)


register_resource_class(Shippings)
register_resource_class(Shipping)
register_resource_class(ShippingPrices)
