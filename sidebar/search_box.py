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
from itools.csv import Table as BaseTable
from itools.datatypes import Decimal, Unicode
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import SelectRadio
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from itws
from itws.repository import BoxAware, register_box
from itws.repository_views import Box_View

# Import from shop
from shop.datatypes import IntegerRange
from shop.search import Shop_ProductSearch, Shop_CategoriesEnumerate
from shop.utils import format_price, get_skin_template



##########################################
## Filter by price
##########################################


class FilterByPrice_BaseTable(BaseTable):

    record_properties = {'min': Decimal,
                         'max': Decimal}


class FilterByPrice_Table(Table):

    class_id = 'filter-by-price-table'
    class_title = MSG(u'Price range')
    class_handler = FilterByPrice_BaseTable


class FilterByPriceBox_View(STLView):

    def get_template(self, resource, context):
        return get_skin_template(context, '/sidebar/search_box/filter_by_price.xml')


    def get_namespace(self, resource, context):
        prices = []
        root = context.root
        site_root = resource.get_site_root()
        shop = site_root.get_resource('shop')

        # query
        abspath = site_root.get_canonical_path()
        prices_resource = resource.get_resource('prices-range')
        get_record_value = prices_resource.handler.get_record_value
        for record in prices_resource.handler.get_records():
            min_price = get_record_value(record, 'min')
            max_price = get_record_value(record, 'max')
            min_price_q = int(min_price * 100) if min_price else None
            max_price_q = int(max_price * 100) if max_price else None
            value = min_price_q, max_price_q
            min_price = format_price(min_price) if min_price else None
            max_price = format_price(max_price) if max_price else None
            checked = context.query.get('range_price') == value
            prices.append({'value': IntegerRange.encode(value),
                           'checked': checked,
                           'css': 'selected' if checked else None,
                           'min': min_price,
                           'max': max_price})
        no_range_price_checked = context.query.get('range_price') == None
        namespace = {'title': resource.get_title(),
                     'no_range_price_checked': no_range_price_checked,
                     'prices': prices}
        return namespace


##########################################
## Search box
##########################################

class SearchBox_View(Box_View):

    categories_widget = SelectRadio
    show_list_categories = True

    query_schema = {
        'product_search_text': Unicode,
        'category': Shop_CategoriesEnumerate(default='*'),
    }

    def get_template(self, resource, context):
        return get_skin_template(context, '/sidebar/search_box/view.xml')


    def get_namespace(self, resource, context):
        namespace = {}
        query = self.get_query(context)
        # Widget with list of categories
        widget = None
        if self.show_list_categories:
            widget = self.categories_widget('category', has_empty_option=False)
            widget = widget.to_html(Shop_CategoriesEnumerate,
                                    value=query['category'])
        # Filter by price
        if resource.get_resource('prices-range', soft=True):
            namespace['filter_by_price'] = FilterByPriceBox_View().GET(resource, context)
        else:
            namespace['filter_by_price'] = None
        # XXX Hack Nb results
        nb_results = None
        if isinstance(context.view, Shop_ProductSearch):
            nb_results = str(context.view.nb_results)
        # Build namespace
        namespace['title'] = resource.get_title()
        namespace['product_search_text'] = query['product_search_text']
        namespace['show_list_categories'] = self.show_list_categories
        namespace['widget_categories'] =  widget
        namespace['nb_results'] = nb_results
        # Return namespace
        return namespace



class SearchBox(BoxAware, Folder):

    class_id = 'sidebar-item-search-box'
    class_title = MSG(u'Search box')
    class_description = MSG(u'Product research box')
    view = SearchBox_View()


register_resource_class(SearchBox)
register_box(SearchBox, allow_instanciation=True)
