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
from itools.datatypes import String
from itools.gettext import MSG
from itools.xapian import AndQuery, OrQuery, NotQuery, PhraseQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.buttons import RemoveButton, RenameButton
from ikaaro.folder_views import Folder_BrowseContent


class Shop_EditorialView(Folder_BrowseContent):
    """
    To delete on 0.62
    """

    access = 'is_allowed_to_edit'
    title = MSG(u'View')

    search_template = '/ui/backoffice/editorial_view.xml'

    table_actions = [RemoveButton, RenameButton]
    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('format', MSG(u'Format')),
        ('workflow_state', MSG(u'State')),
        ]

    def get_query_schema(self):
        return merge_dicts(Folder_BrowseContent.get_query_schema(self),
                           sort_by=String(default='format'))


    def get_items(self, resource, context, *args):
        path = str(resource.parent.get_canonical_path())
        query = [
            PhraseQuery('parent_path', path),
            NotQuery(PhraseQuery('name', '404')),
            OrQuery(PhraseQuery('format', 'shop-section'),
                    PhraseQuery('format', 'products-feed'),
                    PhraseQuery('format', 'webpage'),
                    PhraseQuery('format', 'news-folder'))]
        return context.root.search(AndQuery(*query))


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'name':
            link = '%s/%s' % (resource.get_property('shop_uri'),
                              brain.name)
            return XMLParser(
                "<a href='%s' target='_blank'>%s</a>" % (link, brain.name))
        return Folder_BrowseContent.get_item_value(self, resource,
                  context, item, column)

