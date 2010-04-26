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
from operator import itemgetter

# Import from itools
from itools.gettext import MSG
from itools.web import STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm
from ikaaro.forms import RTEWidget, XHTMLBody
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.views import BrowseForm



class Shippings_Configure(AutoForm):

    access = 'is_admin'
    title = MSG(u'Configure')

    schema = {'msg_if_no_shipping': XHTMLBody(mandatory=True)}

    widgets = [
        RTEWidget('msg_if_no_shipping',
                  title=MSG(u'Message if no shipping available')),
        ]


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        resource.set_property('msg_if_no_shipping',
                              form['msg_if_no_shipping'])
        # Come back
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


class Shippings_History(BrowseForm):

    title = MSG(u'Shippings history')
    access = 'is_admin'

    table_columns = [
        ('complete_id', MSG(u'Id')),
        ('ref', MSG(u'Ref')),
        ('ts', MSG(u'Date')),
        ('shipping_mode', MSG(u'Shipping mode')),
        ('state', MSG(u'State')),
        ]

    def get_items(self, resource, context):
        return resource.get_shippings_items(context)


    def sort_and_batch(self, resource, context, items):
        # Sort
        sort_by = context.query['sort_by']
        reverse = context.query['reverse']
        if sort_by:
            items.sort(key=itemgetter(sort_by), reverse=reverse)

        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        if column == 'ref':
            href = '../orders/%s' % item['ref']
            return item[column], href
        return item[column]



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
                edit_link = context.get_link(prices_resource)
                edit_link += '/?zone=%i&search=' % zone.id
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
                     'edit_link': edit_link})
            namespace['zones'].append({'title': zone_title,
                                       'countries': countries,
                                       'tarifications': tarifications})
        return namespace



