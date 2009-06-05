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
from itools.datatypes import Boolean, Decimal, Unicode
from itools.gettext import MSG
from itools.xml import XMLParser
from itools.web import STLView

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, TextWidget, BooleanCheckBox, MultilineWidget
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.table_views import Table_View
from ikaaro.views import BrowseForm

# Import from shop
from shipping_way import ShippingWay
from schema import delivery_schema


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
        """ Here we concatanate payments off all payment's mode """
        items = []
        for shipping_way in resource.search_resources(cls=ShippingWay):
            items += shipping_way.get_namespace_shippings(context)
        return items


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        if column == 'ref':
            href = '../orders/%s' % item['ref']
            return item[column], href
        return item[column]
