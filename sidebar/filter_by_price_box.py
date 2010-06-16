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
from itools.xapian import AndQuery, PhraseQuery, RangeQuery

# Import from ikaaro
from ikaaro.registry import register_resource_class
from ikaaro.utils import get_base_path_query

# Import from itws
from itws.repository import Box
from itws.repository_views import Box_View



class FilterByPriceBox_View(Box_View):

    title = MSG(u'Filtrer par prix')
    template = '/ui/vertical_depot/filter_by_price_box.xml'

    def get_manage_buttons(self, resource, context):
        return []


    def get_namespace(self, resource, context):
        prices = []
        root = context.root
        site_root = resource.get_site_root()
        shop = site_root.get_resource('shop')

        # query
        abspath = site_root.get_canonical_path()
        for title, min, max in [(MSG(u'200 to 5000€'), 200, 5000)]:
            min = min * 100 if min else None
            max = max * 100 if max else None
            query = [PhraseQuery('format', shop.product_class.class_id),
                     RangeQuery('stored_price', min, max),
                     PhraseQuery('categories', resource.name),
                     PhraseQuery('workflow_state', 'public'),
                     get_base_path_query(str(abspath))]
            results = root.search(AndQuery(*query))
            prices.append({'title': title,
                           'quantity': len(results),
                           'min': min,
                           'max': max})
        namespace = {'title': self.title.gettext(),
                     'prices': prices}
        return namespace



class FilterByPriceBox(Box):

    class_id = 'vertical-item-filter-by-price-box'
    class_title = MSG(u'Vertical item filter by price')
    view = FilterByPriceBox_View()


register_resource_class(FilterByPriceBox)
