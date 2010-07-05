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
from itools.core import merge_dicts
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from shop.shipping
from colissimo import Colissimo
from withdrawal import Withdrawal
from shippings_views import ShippingsView, shippings_schema
from shippings_views import Shippings_Configure, Shippings_Details
from shipping_way import ShippingWay
from shop.folder import ShopFolder
from shop.utils import format_price



class Shippings(ShopFolder):

    class_id = 'shippings'
    class_title = MSG(u'Shipping')
    class_version = '20100502'
    class_views = ['details', 'details_inactive', 'view', 'configure']

    # Views
    view = ShippingsView()
    configure = Shippings_Configure()
    details = Shippings_Details()
    details_inactive = Shippings_Details(show_inactive=True,
                                         title=MSG('Inactive Shippings details'))

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           shippings_schema)


    def get_document_types(self):
        return [ShippingWay, Colissimo, Withdrawal]


    def get_namespace_shipping_ways(self, context, country, infos):
        namespace = []
        # Always add withdrawal if enabled
        for mode in self.search_resources(cls=Withdrawal):
            widget = mode.get_widget_namespace(context, country, [])
            if widget is not None:
                namespace.append(widget)
        # Specific shipping way ?
        specific_delivery_widgets = []
        for name, kw in infos.items():
            if name != 'default':
                mode = context.root.get_resource(name)
                widget = mode.get_widget_namespace(
                            context, country, kw['list_weight'])
                if widget is not None:
                    specific_delivery_widgets.append(widget)
                else:
                    if infos.get('default') is None:
                        infos['default'] = {'list_weight': [],
                                            'nb_products': 0}
                    infos['default']['list_weight'].extend(kw['list_weight'])
                    infos['default']['nb_products'] += kw['nb_products']
        # Get default delivery
        # (Products for wich we don't asign a specific delivery)
        default_delivery = infos.get('default')
        default_delivery_widgets = []
        if default_delivery:
            # XXX We can be cheaper by calculate sum of
            # delivery one by one
            for mode in self.search_resources(cls=ShippingWay):
                if mode.class_id == Withdrawal.class_id:
                    continue
                widget = mode.get_widget_namespace(context, country,
                    default_delivery['list_weight'])
                if widget is not None:
                    default_delivery_widgets.append(widget)
        # If has specific shipping way, we only select
        # first default shipping way
        # XXX take cheaper ?
        if len(specific_delivery_widgets) >= 1 and default_delivery_widgets:
            specific_delivery_widgets.append(default_delivery_widgets[0])
        elif default_delivery_widgets:
            namespace.extend(default_delivery_widgets)
        # Mixed or not ?
        if len(specific_delivery_widgets) > 1:
            namespace.append(
                self.get_default_shipping_way(context,
                      specific_delivery_widgets))
        else:
            namespace.extend(specific_delivery_widgets)
        return namespace


    def get_default_shipping_way(self, context, widgets):
        if len(widgets) == 1:
            return widgets[0]
        price = decimal('0')
        for widget in widgets:
            price += widget['price']
        logo_uri = self.get_property('default_shipping_way_logo')
        logo = self.get_resource(logo_uri, soft=True)
        return {
            'title': self.get_property('default_shipping_way_title'),
            'description': self.get_property('default_shipping_way_description'),
            'enabled': True,
            'img': context.resource.get_pathto(logo) if logo else None,
            'name': 'default',
            'pretty_price': format_price(price),
            'price': price}


    def get_price(self, shipping_way, country, purchase_weight):
        shipping_way = self.get_resource(shipping_way)
        return shipping_way.get_price(country, purchase_weight)


    def get_namespace_shipping_way(self, context, name, country, weight):
        shipping = self.get_resource(name)
        return shipping.get_widget_namespace(context, country, weight)


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


    def update_20100502(self):
        site_root = self.get_site_root()
        for language in site_root.get_property('website_languages'):
            value = self.get_property('msg_if_no_shipping')
            self.del_property('msg_if_no_shipping')
            self.set_property('msg_if_no_shipping', value, language)



register_resource_class(Shippings)
