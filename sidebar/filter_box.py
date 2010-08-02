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
from copy import deepcopy

# Import from itools
from itools.csv import Table as BaseTable
from itools.datatypes import Decimal
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from itws
from itws.repository import BoxAware, register_box
from itws.repository_views import Box_View

# Import from shop
from shop.datatypes import IntegerRange
from shop.utils import format_price, get_skin_template



##########################################
## Filter by price
##########################################


class FilterByPrice_BaseTable(BaseTable):

    record_properties = {'min': Decimal,
                         'max': Decimal}


class FilterByPrice_Table(Table):

    class_id = 'table-filter-by-price'
    class_title = MSG(u'Price range')
    class_handler = FilterByPrice_BaseTable

    form = [TextWidget('min', title=MSG(u'Min')),
            TextWidget('max', title=MSG(u'Max'))]


class FilterByPriceBox_View(STLView):

    def get_template(self, resource, context):
        return get_skin_template(context, '/sidebar/filter_box/filter_by_price.xml')


    def get_namespace(self, resource, context):
        prices = []
        root = context.root
        site_root = resource.get_site_root()
        shop = site_root.get_resource('shop')

        # query
        abspath = site_root.get_canonical_path()
        prices_resource = resource.get_resource('prices-range')
        get_record_value = prices_resource.handler.get_record_value
        uri = deepcopy(context.uri)
        for record in prices_resource.handler.get_records():
            min_price = get_record_value(record, 'min')
            max_price = get_record_value(record, 'max')
            min_price_q = int(min_price * 100) if min_price else None
            max_price_q = int(max_price * 100) if max_price else None
            value = min_price_q, max_price_q
            min_price = format_price(min_price) if min_price else None
            max_price = format_price(max_price) if max_price else None
            checked = context.query.get('range_price') == value
            range_price = IntegerRange.encode(value)
            uri = uri.replace(range_price=range_price)
            prices.append({'href': uri,
                           'checked': checked,
                           'css': 'selected' if checked else None,
                           'min': min_price,
                           'max': max_price})
        # all prices:
        no_range_price_checked = context.query.get('range_price') == None
        all_prices = {'css': 'selected' if no_range_price_checked else None,
                      'href': context.uri.replace(range_price=None)}
        # Build namespace
        namespace = {'title': resource.get_title(),
                     'all_prices': all_prices,
                     'prices': prices}
        return namespace

##########################################
## Filter box
##########################################

class FilterBox_View(Box_View):

    show_list_categories = True

    def get_template(self, resource, context):
        return get_skin_template(context, '/sidebar/filter_box/view.xml')


    def get_namespace(self, resource, context):
        namespace = {}
        # Build namespace
        namespace['title'] = resource.get_title()
        # Filter by price
        namespace['filter_by_price'] = FilterByPriceBox_View().GET(resource, context)
        # Return namespace
        return namespace



class FilterBox(BoxAware, Folder):

    class_id = 'sidebar-item-filter-box'
    class_title = MSG(u'Filter box')
    class_description = MSG(u'Filter box')
    view = FilterBox_View()

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create group
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Filter by price table
        cls = FilterByPrice_Table
        cls._make_resource(cls, folder, '%s/prices-range' % name)


register_resource_class(FilterBox)
register_box(FilterBox, allow_instanciation=True)
