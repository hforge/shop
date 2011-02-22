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
from itools.xapian import PhraseQuery
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import SelectWidget
from ikaaro.registry import register_resource_class

# Import from itws
from itws.views import AutomaticEditView

# Import from shop
from categories_views import Category_View
from products.enumerate import ProductModelsEnumerate


class CrossSelling_Section_View(Category_View):

    def get_items(self, resource, context, *args):
        product_model = resource.get_property('product_model')
        query = PhraseQuery('product_model', product_model)
        return context.root.search(query)



class CrossSelling_Section(Folder):
    """
    XXX That should be a section_view on 0.62
    """

    class_id = 'section-cross-selling'
    class_title = MSG(u'Cross Selling Section')
    class_views = ['view', 'edit']

    view = CrossSelling_Section_View()
    edit = AutomaticEditView()

    # Edit views
    edit_schema = {'product_model': ProductModelsEnumerate}

    edit_widgets = [
            SelectWidget('product_model', title=MSG(u'Product model')),
            ]



register_resource_class(CrossSelling_Section)
