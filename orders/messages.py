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
from itools.csv import Table as BaseTable
from itools.datatypes import Boolean, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime

# Import from ikaaro
from ikaaro.forms import BooleanCheckBox, TextWidget, MultilineWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table


class Messages_TableHandler(BaseTable):

    record_schema = {'author': String,
                     'message': Unicode,
                     'private': Boolean,
                     'seen': Boolean(is_indexed=True)}



class Messages_TableResource(Table):

    class_id = 'shop-order-messages'
    class_title = MSG(u'Messages')
    class_handler = Messages_TableHandler
    class_version = '20091126'

    form = [TextWidget('author', title=MSG(u'Author')),
            MultilineWidget('message', title=MSG(u'Message')),
            BooleanCheckBox('private', title=MSG(u'Private ?')),
            BooleanCheckBox('seen', title=MSG(u'Seen ?'))]

    def get_namespace_messages(self, context):
        messages = []
        get_value = self.handler.get_record_value
        for record in self.handler.get_records():
            author = get_value(record, 'author')
            author = context.root.get_resource('/users/%s' % author)
            ts = get_value(record, 'ts')
            messages.append({'id': record.id,
                             'author': author.get_title(),
                             'message': get_value(record, 'message'),
                             'private': get_value(record, 'private'),
                             'seen': get_value(record, 'seen'),
                             'ts': format_datetime(ts, context.accept_language)})
        return messages


    def update_20091126(self):
        for record in self.handler.get_records():
            self.handler.update_record(record.id, **{'seen': True})


register_resource_class(Messages_TableResource)
