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
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.web import STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, ImageSelectorWidget, MultilineWidget
from ikaaro.forms import RTEWidget, TextWidget, XHTMLBody
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.resource_views import EditLanguageMenu

# Import from shop
from shop.utils import bool_to_img

# XXX msg_if_no_shipping must be multilingual

shippings_schema = {
    'default_shipping_way_title': Unicode(mandatory=True, multilingual=True),
    'default_shipping_way_logo': String(mandatory=True),
    'default_shipping_way_description': Unicode(mandatory=True, multilingual=True),
    'msg_if_no_shipping': XHTMLBody(mandatory=True, multilingual=True)}


class Shippings_Configure(AutoForm):

    access = 'is_admin'
    title = MSG(u'Configure')
    context_menus = [EditLanguageMenu()]

    schema = shippings_schema

    widgets = [
        TextWidget('default_shipping_way_title',
                  title=MSG(u'Default shipping way title')),
        ImageSelectorWidget('default_shipping_way_logo',
                  title=MSG(u'Default shipping way logo')),
        MultilineWidget('default_shipping_way_description',
                  title=MSG(u'Default shipping way description')),
        RTEWidget('msg_if_no_shipping',
                  title=MSG(u'Message if no shipping available')),
        ]


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name) or datatype.get_default()


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key, datatype in self.get_schema(resource, context).items():
            if getattr(datatype, 'multilingual', False):
                resource.set_property(key, form[key], language)
            else:
                resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)



class ShippingsView(Folder_BrowseContent):

    access = 'is_admin'
    title = MSG(u'Shippings')

    # Configuration
    table_actions = []
    search_template = None

    table_columns = [
        ('checkbox', None),
        ('logo', None),
        ('title', MSG(u'Title')),
        ('description', MSG(u'Description')),
        ('enabled', MSG(u'Enabled ?')),
        ]


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'logo':
            logo = '<img src="%s"/>' % item_resource.get_logo(context)
            return XMLParser(logo)
        elif column == 'enabled':
            value = item_resource.get_property(column)
            return MSG(u'Yes') if value else MSG(u'No')
        elif column == 'title':
            return item_resource.get_title(), item_brain.name
        elif column == 'description':
            return item_resource.get_property(column)
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)



class Shippings_Details(STLView):

    title = MSG(u'Shippings details')
    access = 'is_admin'
    template = '/ui/shop/shipping/shippings_details.xml'

    # Should
    show_inactive = False

    def get_namespace(self, resource, context):
        resource_zones = resource.get_resource('../countries-zones')
        handler_countries = resource.get_resource('../countries').handler
        if self.show_inactive:
            page_title = MSG('Inactives shippings prices')
        else:
            page_title = MSG('Shippings price')
        namespace = {
            'zones': [],
            'msg_if_no_shipping': resource.get_property('msg_if_no_shipping'),
            'page_title': page_title}
        for zone in resource_zones.handler.get_records_in_order():
            countries = []
            for country in handler_countries.search(zone=str(zone.id)):
                title = handler_countries.get_record_value(country, 'title')
                if handler_countries.get_record_value(country, 'enabled') is False:
                    continue
                countries.append(title)
            if len(countries) == 0:
                continue
            zone_title = resource_zones.handler.get_record_value(zone, 'title')
            tarifications = []
            for tarification in resource.get_resources():
                # We show only active or inactives modes, depending on config
                if tarification.get_property('enabled') is self.show_inactive:
                    continue
                mode = tarification.get_property('mode')
                unit = MSG(u'Kg') if mode == 'weight' else MSG(u'Unit')
                prices = []
                min = old_price = 0
                prices_resource = tarification.get_resource('prices')
                prices_handler = prices_resource.handler
                tarif_edit = context.get_link(prices_resource)
                tarif_edit += '/?zone=%i&search=' % zone.id
                records = prices_handler.search(zone=str(zone.id))
                records.sort(key=lambda x: prices_handler.get_record_value(x, 'max-%s' % mode))
                for price in records:
                    max = prices_handler.get_record_value(price, 'max-%s' % mode)
                    price = prices_handler.get_record_value(price, 'price')
                    prices.append(
                      {'title': '%s to %s %s' % (min, max, unit.gettext()),
                       'price': price,
                       'error': price<=old_price})
                    min = max
                    old_price = price
                if len(prices) == 0:
                    continue
                tarifications.append(
                    {'name': tarification.name,
                     'title': tarification.get_title(),
                     'img': tarification.get_property('logo'),
                     'is_free': tarification.get_property('is_free'),
                     'prices': prices,
                     'description': tarification.get_property('description'),
                     'tarif_edit': tarif_edit})
            zone_edit = '/shop/countries?zone=%i&search=' % zone.id
            has_tax = resource_zones.handler.get_record_value(zone, 'has_tax')
            tax_image = list(bool_to_img(has_tax))
            namespace['zones'].append({'title': zone_title,
                                       'countries': countries,
                                       'tarifications': tarifications,
                                       'zone_edit': zone_edit,
                                       'tax_image': tax_image})
        return namespace



