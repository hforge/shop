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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from shop.shipping
from colissimo import Colissimo
from withdrawal import Withdrawal
from shippings_views import ShippingsView, Shippings_History
from shipping_way import ShippingWay



class Shippings(Folder):

    class_id = 'shippings'
    class_title = MSG(u'Shipping')
    class_views = ['view', 'history']


    # Views
    view = ShippingsView()
    history = Shippings_History()


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Init with some shippings mode
        for c in [Colissimo, Withdrawal]:
            kw = {'title': {'en': c.class_title.gettext()},
                  'description': {'en': c.class_description.gettext()}}
            c._make_resource(c, folder, '%s/%s' % (name, c.class_id), **kw)



    def get_document_types(self):
        return []


    def get_price(self, shipping_way, country, purchase_price,
                  purchase_weight):
        shipping_way = self.get_resource(shipping_way)
        return shipping_way.get_price(country, purchase_price, purchase_weight)


    #def get_shipping_ways(self, country, purchase_price, purchase_weight):
    #    ways = []
    #    for mode in self.search_resources(cls=ShippingWay):


    def get_namespace_shipping_ways(self, context, country, price, weight):
        namespace = []
        for mode in self.search_resources(cls=ShippingWay):
            if not mode.get_property('enabled'):
                continue
            widget = mode.get_widget_namespace(context, country, price, weight)
            if widget:
                namespace.append(widget)
        # XXX If no price corresponding to options,
        # we should set a default price.
        return namespace


    def get_namespace_shipping_way(self, context, name, country, price, weight):
        shipping = self.get_resource(name)
        if not shipping.get_property('enabled'):
            return None
        return shipping.get_widget_namespace(context, country, price, weight)


    def get_shippings_items(self, context, ref=None):
        items = []
        for shipping_way in self.search_resources(cls=ShippingWay):
            history = shipping_way.get_resource('history')
            if ref:
                records = history.handler.search(ref=ref)
            else:
                records = history.handler.get_records()
            for record in records:
                items.append(history.get_record_namespace(context, record))
        return items


    def get_shippings_records(self, context, ref=None):
        records = []
        for shipping_way in self.search_resources(cls=ShippingWay):
            history = shipping_way.get_resource('history')
            if ref:
                records.extend(history.handler.search(ref=ref))
            else:
                records.extend(history.handler.get_records())
        return records


register_resource_class(Shippings)
