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
from itools.datatypes import Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import SelectRadio
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import BarItem, register_bar_item
from itws.repository_views import BarItem_View

# Import from shop
from shop.search import Shop_ProductSearch, Shop_CategoriesEnumerate



class SearchBox_View(BarItem_View):

    template = '/ui/vertical_depot/search_box.xml'

    query_schema = {
        'product_search_text': Unicode,
        'category': Shop_CategoriesEnumerate(default='*'),
    }

    categories_widget = SelectRadio
    show_list_categories = True

    def get_namespace(self, resource, context):
        query = self.get_query(context)
        # Widget with list of categories
        widget = None
        if self.show_list_categories:
            widget = self.categories_widget('category', has_empty_option=False)
            widget = widget.to_html(Shop_CategoriesEnumerate,
                                    value=query['category'])
        # XXX Hack Nb results
        nb_results = None
        if isinstance(context.view, Shop_ProductSearch):
            nb_results = str(context.view.nb_results)
        # Return namespace
        return {'title': resource.get_title(),
                'product_search_text': query['product_search_text'],
                'show_list_categories': self.show_list_categories,
                'widget_categories': widget,
                'nb_results': nb_results}



class SearchBox(BarItem):

    class_id = 'sidebar-item-search-box'
    class_title = MSG(u'Search box')
    view = SearchBox_View()


register_resource_class(SearchBox)
register_bar_item(SearchBox, allow_instanciation=True)
