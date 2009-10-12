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
from itools.datatypes import Enumerate, PathDataType
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import XHTMLBody
from ikaaro.registry import register_resource_class

# Import from shop
from manufacturers_views import Manufacturer_Add
from manufacturers_views import manufacturer_schema, Manufacturers_View
from manufacturers_views import Manufacturer_View, Manufacturer_Edit
from utils import CurrentFolder_AddImage, get_shop, ShopFolder



class ManufacturersEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        shop = get_shop(context.resource)
        manufacturers = shop.get_resource('manufacturers')
        return [{'name': res.get_abspath(),
                 'value': res.get_title()}
                   for res in manufacturers.get_resources()]



class Manufacturer(Folder):

    class_id = 'manufacturer'
    class_title = MSG(u'Manufacturer')
    class_views = ['view', 'edit']

    view = Manufacturer_View()
    edit = Manufacturer_Edit()
    add_image = CurrentFolder_AddImage()


    @classmethod
    def get_metadata_schema(cls):
        return manufacturer_schema




class Manufacturers(Folder):

    class_id = 'manufacturers'
    class_title = MSG(u'Manufacturers')
    class_views = ['view', 'add']

    view = Manufacturers_View()
    add = Manufacturer_Add()

    def get_document_types(self):
        return [Manufacturer]



class VirtualManufacturers(Manufacturers):

    class_id = 'virtual-manufacturers'

    def _get_resource(self, name):
        shop = get_shop(self)
        manufacturer = shop.get_resource('manufacuters/%s' % name, soft=True)
        if manufacturer is None:
            return None
        # Build another instance with the same properties
        return Manufacturer(manufacturer.metadata)

# Register
register_resource_class(Manufacturers)
register_resource_class(VirtualManufacturers)
register_resource_class(Manufacturer)
