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

# Import from shop
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


class Shipping_View(STLView):

    access = 'is_admin'
    title = MSG(u'Shipping')

    template = '/ui/shop/shipping/view.xml'

    def get_namespace(self, resource, context):
        return resource.get_namespace(context)


class Shipping_Configure(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')

    schema = delivery_schema

    widgets = [
        TextWidget('title', title=MSG(u'Title')),
        MultilineWidget('description', title=MSG(u'Description')),
        BooleanCheckBox('enabled', title=MSG(u'Enabled ?')),
        ]


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        for key in self.schema.keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED)
