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
from itools.xapian import PhraseQuery

# Import from ikaaro
from ikaaro.forms import BooleanRadio, TextWidget
from ikaaro.registry import register_resource_class

# Import from itws
from itws.repository import Box, register_box
from itws.repository_views import Box_View

# Import from shop
from shop.utils_views import Viewbox_View


class LastUsersBox_View(Box_View, Viewbox_View):


    def get_items_search(self, resource, context, *args):
        query = PhraseQuery('format', 'user')
        return context.root.search(query)


    def get_nb_items_to_show(self, resource):
        return resource.get_property('nb_items_to_show')



class LastUsersBox(Box):

    class_id = 'shop_sidebar_last_users'
    class_title = MSG(u'Bar that list last users')
    class_description = MSG(u'Bar that list last users that registred into website')

    view = LastUsersBox_View()

    edit_schema = {'show_title': Boolean,
                   'nb_items_to_show': Integer}
    edit_widgets = [BooleanRadio('show_title', title=MSG(u'Show title ?')),
                    TextWidget('nb_items_to_show', title=MSG(u'Nb users to show ?'))]



register_resource_class(LastUsersBox)
register_box(LastUsersBox, allow_instanciation=True,
             is_content=True, is_side=False)
