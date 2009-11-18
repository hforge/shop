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
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from shop
from suppliers_views import Suppliers_View, Supplier_Add, Supplier_Edit
from suppliers_views import supplier_schema
from utils import CurrentFolder_AddImage, get_shop



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
    class_views = ['view', 'edit']

    edit = Supplier_Edit()
    add_image = CurrentFolder_AddImage()
    new_instance = Supplier_Add()


    @classmethod
    def get_metadata_schema(cls):
        return supplier_schema




class Suppliers(Folder):

    class_id = 'suppliers'
    class_title = MSG(u'Suppliers')
    class_views = ['browse_content', 'add']

    browse_content = Suppliers_View()
    add = Supplier_Add()

    def get_document_types(self):
        return [Supplier]



# Register
register_resource_class(Suppliers)
register_resource_class(Supplier)
