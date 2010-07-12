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
from itools.datatypes import PathDataType
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import XHTMLBody, ImageSelectorWidget, RTEWidget

# Import from itws
from itws.views import AutomaticEditView

# Import from shop
from datatypes import DynamicEnumerate
from manufacturers_views import Manufacturer_Add
from manufacturers_views import Manufacturers_View
from manufacturers_views import Manufacturer_View
from utils import CurrentFolder_AddImage



class ManufacturersEnumerate(DynamicEnumerate):

    path = '/'
    format = 'manufacturer'
    is_abspath = True



class Manufacturer(Folder):

    class_id = 'manufacturer'
    class_title = MSG(u'Manufacturer')
    class_views = ['view', 'edit']

    view = Manufacturer_View()
    edit = AutomaticEditView()
    add_image = CurrentFolder_AddImage()
    new_instance = Manufacturer_Add()

    # Edit configuration
    edit_show_meta = True
    edit_schema = {'data': XHTMLBody(mandatory=True, multilingual=True),
                   'photo': PathDataType(mandatory=True)}

    edit_widgets = [
            ImageSelectorWidget('photo', title=MSG(u'Photo')),
            RTEWidget('data', title=MSG(u'Data'))]


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(Folder.get_metadata_schema(),
                           data=XHTMLBody,
                           photo=PathDataType)




class Manufacturers(Folder):

    class_id = 'manufacturers'
    class_title = MSG(u'Manufacturers')
    class_views = ['view', 'edit', 'add']

    view = Manufacturers_View()
    add = Manufacturer_Add()

    def get_document_types(self):
        return [Manufacturer]
