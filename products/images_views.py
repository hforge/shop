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
from itools.gettext import MSG
from itools.web import FormError
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.table_views import OrderedTable_View, Table_AddRecord
from ikaaro.table_views import Table_EditRecord
from ikaaro.views import CompositeForm



class PhotoOrderedTable_TableView(OrderedTable_View):

    def get_table_columns(self, resource, context):
        columns = OrderedTable_View.get_table_columns(self, resource, context)
        columns = columns[:2]
        columns.append(('image', MSG(u'Image')))
        columns.append(('title', MSG(u'Title')))
        columns.append(('description', MSG(u'Description')))
        columns.append(('order', MSG(u'Order')))

        return columns


    def get_item_value(self, resource, context, item, column):
        gallery = resource.parent
        if column == 'image':
            image = None
            try:
                image = resource.get_resource(item.name)
            except LookupError:
                # XXX fallback
                try:
                    image = gallery.get_resource(item.name)
                except LookupError:
                    return None
            link = context.get_link(image)
            src = '%s/;thumb?width=%s&amp;height=%s' % (link, 50, 50)
            preview = '<img src="%s" />' % src
            return XMLParser(preview)
        elif column in ('description', 'title'):
            try:
                image = resource.get_resource(item.name)
            except LookupError:
                # XXX fallback
                try:
                    image = gallery.get_resource(item.name)
                except LookupError:
                    return None
            return image.get_property(column)
        return OrderedTable_View.get_item_value(self, resource, context,
                                                item, column)



class PhotoOrderedTable_AddRecord(Table_AddRecord):

    title = MSG(u'New photo')

    def _get_form(self, resource, context):
        form = Table_AddRecord._get_form(self, resource, context)
        # We check if the image path refer to an Image instance
        path = form['name']
        check_photo(path, resource, 'name')
        return form


    def action_on_success(self, resource, context):
        return context.come_back(MSG(u'New record added.'))



class PhotoOrderedTable_EditRecord(Table_EditRecord):

    title = MSG(u'Change photo')

    def _get_form(self, resource, context):
        form = Table_EditRecord._get_form(self, resource, context)
        # We check if the image path refer to an Image instance
        path = form['name']
        check_photo(path, resource, 'name')
        return form



class PhotoOrderedTable_View(CompositeForm):

    access = 'is_allowed_to_edit'

    title = MSG(u'Manage photos')

    subviews = [PhotoOrderedTable_AddRecord(),
                PhotoOrderedTable_TableView()]

    def _get_form(self, resource, context):
        form = CompositeForm._get_form(self, resource, context)
        if 'name' in form:
            # We check if the image path refer to an Image instance
            path = form['name']
            check_photo(path, resource, 'name')
        return form



def check_photo(path, resource, form_key):
    """ check if the path refer to an Image instance
    """
    if path:
        img_resource = resource.get_resource(str(path), soft=True)
        if not img_resource or not isinstance(img_resource, Image):
            raise FormError(invalid=[form_key])
    else:
        raise FormError(invalid=[form_key])
