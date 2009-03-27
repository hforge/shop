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
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.table_views import OrderedTable_View



class PhotoOrderedTable_View(OrderedTable_View):

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

