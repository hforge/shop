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
from itools.core import merge_dicts
from itools.datatypes import Enumerate, Email, Unicode, String
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget, MultilineWidget
from ikaaro.registry import register_resource_class

# Import from itws
from itws.views import AutomaticEditView

# Import from shop
from suppliers_views import Suppliers_View
from utils import CurrentFolder_AddImage, get_shop


# XXX use AbspathEnumerate
class SuppliersEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        shop = get_shop(context.resource)
        suppliers = shop.get_resource('suppliers')
        return [{'name': res.get_abspath(),
                 'value': res.get_title()}
                   for res in suppliers.get_resources()]



class Supplier(Folder):

    class_id = 'supplier'
    class_title = MSG(u'Supplier')
    class_views = ['edit']

    edit = AutomaticEditView()
    add_image = CurrentFolder_AddImage()

    # Edit views
    edit_schema = {'address': Unicode(mandatory=True),
                   'phone': String,
                   'fax': String,
                   'email': Email,
                   'description': Unicode(multilingual=True)}

    edit_widgets = [
            MultilineWidget('address', title=MSG(u'Address')),
            TextWidget('phone', title=MSG(u'Phone')),
            TextWidget('fax', title=MSG(u'Fax')),
            TextWidget('email', title=MSG(u'Email')),
            MultilineWidget('description', title=MSG(u'Description'))
            ]


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           cls.edit_schema)




class Suppliers(Folder):

    class_id = 'suppliers'
    class_title = MSG(u'Suppliers')
    class_views = ['browse_content']

    browse_content = Suppliers_View()

    def get_document_types(self):
        return [Supplier]



# Register
register_resource_class(Suppliers)
register_resource_class(Supplier)
