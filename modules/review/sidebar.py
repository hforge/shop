# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Boolean, Integer
from itools.gettext import MSG
from itools.xapian import AndQuery, PhraseQuery, RangeQuery

# Import from ikaaro
from ikaaro.forms import BooleanRadio, TextWidget
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import Box, register_box
from itws.repository_views import Box_View

# Import from shop
from shop.utils_views import Viewbox_View
from shop.datatypes import IntegerRangeDatatype
from shop.widgets import NumberRangeWidget


class ReviewBox_View(Box_View, Viewbox_View):

    sort_by = 'ctime'
    sort_reverse = True

    def get_items_search(self, resource, context, *args):
        min_v, max_v = resource.get_property('note_range')
        queries = [PhraseQuery('format', 'shop_module_a_review'),
                   PhraseQuery('workflow_state', 'public'),
                   RangeQuery('shop_module_review_note', min_v, max_v)]
        return context.root.search(AndQuery(*queries))


    def get_nb_items_to_show(self, resource):
        return resource.get_property('nb_items_to_show')



class ReviewBox(Box):

    class_id = 'shop_module_review_sidebar'
    class_title = MSG(u'Bar that list last reviews')
    class_description = MSG(u'Bar that list last reviews')

    view = ReviewBox_View()

    edit_schema = {'show_title': Boolean,
                   'nb_items_to_show': Integer,
                   'note_range': IntegerRangeDatatype(default=[0, 5])}

    edit_widgets = [BooleanRadio('show_title', title=MSG(u'Show title ?')),
                    TextWidget('nb_items_to_show', title=MSG(u'Numbers of items to show ?')),
                    NumberRangeWidget('note_range', title=MSG(u'Note range'))]


register_resource_class(ReviewBox)
register_box(ReviewBox, allow_instanciation=True,
             is_content=True, is_side=False)
