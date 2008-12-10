# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from standard library

# Import from itools
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.web import STLView

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent

# Import from package


class OrderPay(STLView):

    access = 'is_allowed_to_view'

    template = '/ui/orders/OrderPay.xml'


class OrdersProductsView(STLView):

    access = 'is_allowed_to_view'

    template = '/ui/orders/OrdersProductsView.xml'



class OrdersView(Folder_BrowseContent):

    access = 'is_admin'
    title = MSG(u'Orders')

    # Configuration
    table_actions = []
    search_template = None

    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('total_price', MSG(u'Total Price')),
        ('creation_datetime', MSG(u'Order datetime'))]


    def get_item_value(self, resource, context, item, column):
        value = Folder_BrowseContent.get_item_value(self, resource, context,
                    item, column)
        if column in ['total_price']:
            return item.get_property(column)
        if column == 'creation_datetime':
            value = item.get_property(column)
            # XXX to delete
            if not value:
                return '-'
            accept = context.accept_language
            return format_datetime(value, accept=accept)
        return value
