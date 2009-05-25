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
from itools.uri import Path
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument, Folder_Orphans
from ikaaro.folder_views import Folder_PreviewContent, Folder_LastChanges
from ikaaro.folder_views import Folder_BrowseContent
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


    def get_links(self):
        # Use the canonical path instead of the abspath
        base = self.get_canonical_path()
        handler = self.handler
        get_value = handler.get_record_value
        links = []

        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            links.append(str(base.resolve2(name)))

        return links


    def change_link(self, old_path, new_path):
        # Use the canonical path instead of the abspath
        base = self.get_canonical_path()
        handler = self.handler
        get_value = handler.get_record_value

        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            path = base.resolve2(name)
            if str(path) == old_path:
                # Hit the old name
                new_path2 = base.get_pathto(Path(new_path))
                handler.update_record(record.id, **{'name': str(new_path2)})

        get_context().server.change_resource(self)



class ImagesFolder(Folder):

    class_id = 'images-folder'
    class_title = MSG(u'Images folder')

    def get_document_types(self):
        return [Image]


    # Views
    browse_content = Folder_BrowseContent(access='is_admin')
    preview_content = Folder_PreviewContent(access='is_admin')
    last_changes = Folder_LastChanges(access='is_admin')
    orphans = Folder_Orphans(access='is_admin')




register_resource_class(PhotoOrderedTable)
register_resource_class(ImagesFolder)
