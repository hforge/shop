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
from itools.csv import Table as BaseTable
from itools.datatypes import Decimal
from itools.gettext import MSG
from itools.handlers import merge_dicts

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from schema import delivery_schema
from shipping_views import ShippingsView, Shipping_Configure



class ShippingPricesTable(BaseTable):

    record_schema = {
      'max-weight': Decimal(mandatory=True),
      'price': Decimal(mandatory=True),
      }



class ShippingPrices(Table):

    class_id = 'shipping-prices'
    class_title = MSG(u'Shipping Prices')
    class_handler = ShippingPricesTable

    class_views = ['view']

    form = [
        TextWidget('max-weight', title=MSG(u'Max Weight (Kg)')),
        TextWidget('price', title=MSG(u'Price'))]



class Shipping(Folder):

    class_id = 'shipping'
    class_title = MSG(u'Shipping')
    class_views = ['configure']

    # Views
    configure = Shipping_Configure()


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Prices
        ShippingPrices._make_resource(ShippingPrices, folder,
                                      '%s/prices' % name)

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(), delivery_schema)


    def get_price(self, price, weight):
        prices = self.get_resource('prices')
        prices_records = list(prices.handler.get_records())
        # If we use base price
        if len(prices_records)==0:
            return self.get_property('base_price')
        # XXX TODO
        return 10.0


    def get_logo(self, context):
        if self.has_resource('logo.png'):
            logo = self.get_resource('logo.png')
            uri = context.get_link(logo)
        else:
            uri = '/ui/icons/48x48/text.png'
        return '%s/;download' % uri


    def get_namespace(self, context, price, weight):
        ns = {'name': self.name,
              'img': self.get_logo(context),
              'title': self.get_title(),
              'price': self.get_price(price, weight)}
        for key in ['description', 'delivery_time', 'enabled']:
            ns[key] = self.get_property(key)
        return ns



class Shippings(Folder):

    class_id = 'shippings'
    class_title = MSG(u'Shipping')
    class_views = ['view', 'new_resource?type=shipping']

    # Views
    view = ShippingsView()


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Init with some shippings mode
        ships = [{'name': 'collisimo',
                  'img': 'ui/shop/images/colissimo.png',
                  'title': u'Collisimo Suivi',
                  'description': u"""La livraison de votre commande est assurée en Colissimo.
                                     A compter de la prise en charge par La Poste,
                                     vous êtes livré à domicile en 48 h(1)
                                      sous réserve des heures limites de dépôt""",
                  'delivery_time': u'48 heures'},
                  {'name': 'no_shipping',
                   'img': 'ui/shop/images/noship.png',
                   'title': u'Retrait au magasin',
                   'delivery_time': u'-'}]
        for ship in ships:
            kw = {'title': {'en': ship['title']},
                  'delivery_time': ship['delivery_time']}
            Shipping._make_resource(Shipping, folder,
                '%s/%s' % (name, ship['name']), **kw)
            # Image
            kw['state'] = 'public'
            body = vfs.open(get_abspath(ship['img'])).read()
            img = Image._make_resource(Image, folder,
                    '%s/%s/logo.png' % (name, ship['name']), body=body, **kw)



    def get_document_types(self):
        return [Shipping]


    def get_ns_shipping_way(self, context, price, weight):
        l = []
        for elt in self.search_resources(cls=Shipping):
            ns = elt.get_namespace(context, price, weight)
            if bool(ns['enabled']) is False:
                continue
            l.append(ns)
        return l


    def get_shipping_namespace(self, context, shipping, price, weight):
        shipping = self.get_resource(shipping)
        return shipping.get_namespace(context, price, weight)


register_resource_class(Shippings)
register_resource_class(Shipping)
register_resource_class(ShippingPrices)
