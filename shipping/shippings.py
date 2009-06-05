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
from shippings_views import ShippingsView
from shipping_way import ShippingWay



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
        for c in [Colissimo, Withdrawal]:
            kw = {'title': {'en': c.class_title.gettext()},
                  'description': {'en': c.class_description.gettext()}}
            c._make_resource(c, folder, '%s/%s' % (name, c.class_id), **kw)



    def get_document_types(self):
        return [ShippingWay]


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



    def get_shippings_records(self, ref=None):
        records = []
        for shipping_way in self.search_resources(cls=ShippingWay):
            history = shipping_way.get_resource('history')
            if ref is None:
                shipping_records = (shipping_way, history.handler.get_records())
            else:
                shipping_records = (shipping_way, history.handler.search(ref=ref))
            records.append(shipping_records)
        return records


    def get_shippings_namespace(self, context, ref=None):
        shippings = []
        for shipping_way, records in self.get_shippings_records(ref):
            table = shipping_way.get_resource('history')
            img = context.get_link(shipping_way.get_resource('logo.png'))
            for record in records:
                ns = table.get_record_namespace(context, record)
                ns['title'] = shipping_way.get_title()
                ns['description'] = shipping_way.get_property('description')
                ns['img'] = img
                shippings.append(ns)
        return shippings



register_resource_class(Shippings)
