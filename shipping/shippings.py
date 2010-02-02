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
from itools.core import merge_dicts
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import XHTMLBody
from ikaaro.registry import register_resource_class

# Import from shop.shipping
from colissimo import Colissimo
from withdrawal import Withdrawal
from shippings_views import ShippingsView, Shippings_History
from shippings_views import Shippings_Configure, Shippings_Details
from shipping_way import ShippingWay
from shop.utils import ShopFolder



class Shippings(ShopFolder):

    class_id = 'shippings'
    class_title = MSG(u'Shipping')
    class_version = '20091022'
    class_views = ['details', 'view', 'configure', 'history']


    # Views
    view = ShippingsView()
    configure = Shippings_Configure()
    history = Shippings_History()
    details = Shippings_Details()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           msg_if_no_shipping=XHTMLBody)


    def get_document_types(self):
        return [ShippingWay, Colissimo, Withdrawal]


    def get_price(self, shipping_way, country, purchase_weight):
        shipping_way = self.get_resource(shipping_way)
        return shipping_way.get_price(country, purchase_weight)


    def get_namespace_shipping_ways(self, context, country, weight):
        namespace = []
        for mode in self.search_resources(cls=ShippingWay):
            if not mode.get_property('enabled'):
                continue
            widget = mode.get_widget_namespace(context, country, weight)
            if widget:
                namespace.append(widget)
        return namespace


    def get_namespace_shipping_way(self, context, name, country, weight):
        shipping = self.get_resource(name)
        if not shipping.get_property('enabled'):
            return None
        return shipping.get_widget_namespace(context, country, weight)


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



    def update_20091022(self):
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        for resource in self.traverse_resources():
            title = resource.get_property('title')
            description = resource.get_property('description')
            resource.del_property('title')
            resource.del_property('description')
            for language in languages:
                resource.set_property('title', title, language)
                resource.set_property('description', description, language)



register_resource_class(Shippings)
