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
from itools.core import merge_dicts
from itools.datatypes import Unicode, DateTime
from itools.gettext import MSG

# Import from ikaaro
from ikaaro import messages
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import title_widget, timestamp_widget
from ikaaro.resource_views import DBResource_Edit


class Modules_View(Folder_BrowseContent):

    access = 'is_admin'
    title = MSG(u'Modules')

    # Configuration
    table_actions = []
    search_template = None

    table_columns = [
        ('title', MSG(u'Title')),
        ('description', MSG(u'Description')),
        ]


    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'title':
            return item_resource.get_title(), item_brain.name
        elif column == 'description':
            return item_resource.class_description
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)



class ShopModule_Edit(DBResource_Edit):

    title = MSG(u'Edit')
    access = 'is_allowed_to_edit'

    base_schema = {'title': Unicode,
                   'timestamp': DateTime(readonly=True)}

    base_widgets = [ timestamp_widget, title_widget ]


    def get_schema(self, resource, context):
        return merge_dicts(self.base_schema, resource.item_schema)


    def get_widgets(self, resource, context):
        return self.base_widgets + resource.item_widgets


    def action(self, resource, context, form):
        # Check edit conflict
        self.check_edit_conflict(resource, context, form)
        if context.edit_conflict:
            return

        # Save changes
        title = form['title']
        language = resource.get_content_language(context)
        resource.set_property('title', title, language=language)
        for key, datatype in resource.item_schema.items():
            if getattr(datatype, 'multilingual', False) is True:
                resource.set_property(key, form[key], language)
            else:
                resource.set_property(key, form[key])

        # Ok
        context.message = messages.MSG_CHANGES_SAVED
