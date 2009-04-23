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
from itools.datatypes import String, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import ImageSelectorWidget
from ikaaro.future.order import ChildrenOrderedTable
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_AddImage
from ikaaro.table import OrderedTableFile

# Import from shop
from images_views import PhotoOrderedTable_View


class PhotoOrderedTableFile(OrderedTableFile):

    record_schema = {'title': Unicode,
                     'description': Unicode,
                     'image': String,
                     'name': String}



class PhotoOrderedTable(ChildrenOrderedTable):

    class_id = 'gallery-ordered-table'
    class_title = MSG(u'Photo Ordered Table')
    class_handler = PhotoOrderedTableFile
    class_views = ['view', 'add_record', 'goto_preview']

    form = [ImageSelectorWidget('name', title=MSG(u'Chemin'))]

    # Views
    view = PhotoOrderedTable_View()
    add_image = DBResource_AddImage()
    goto_preview = GoToSpecificDocument(specific_document='..',
                                 title=MSG(u'See product'))


    def get_orderable_classes(self):
        return (Image,)


    def get_add_bc_root(self, add_type, target_id):
        # return "images" folder
        return self.get_resource('../images')


register_resource_class(PhotoOrderedTable)
