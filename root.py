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

# Import from standard library
import traceback

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Email, MultiLinesTokens
from itools.gettext import MSG
from itools.stl import stl

# Import from ikaaro
from ikaaro.database import ReadOnlyDatabase
from ikaaro.forms import MultilineWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import DBResource_Edit
from ikaaro.root import Root as BaseRoot

# Import from shop
from utils import get_skin_template


class ShopRoot_Edit(DBResource_Edit):

    access = 'is_admin'

    schema = {'administrators': MultiLinesTokens(mandatory=True)}
    widgets = [MultilineWidget('administrators', title=MSG(u"Administrators"))]

    def action(self, resource, context, form):
        values = [x.strip() for x in form['administrators']]
        resource.set_property('administrators', values)
        context.message = MSG_CHANGES_SAVED
        return


internal_error_body = MSG(u"""
**Website**

{uri}

**Error**

{error}

**Headers**

{headers}
""")


class Root(BaseRoot):

    class_id = 'iKaaro'

    edit = ShopRoot_Edit()

    @classmethod
    def get_metadata_schema(cls):
        # XXX Administrator must be a role
        return merge_dicts(BaseRoot.get_metadata_schema(),
                           administrators=Email(multiple=True))


    def internal_server_error(self, context):
        # We send an email to administrators
        for email in self.get_property('administrators'):
            subject = MSG(u'Internal server error').gettext()
            headers = u'\n'.join([u'%s => %s' % (x, y)
                                    for x, y in context.get_headers()])
            text = internal_error_body.gettext(uri=context.uri,
                error=traceback.format_exc(), headers=headers)
            self.send_email(email, subject, text=text)
        # We show a prerry error page
        database = context.database
        namespace = {'traceback': '',
                     'read_only': type(database) is ReadOnlyDatabase}
        handler = get_skin_template(context, 'internal_server_error.xml')
        return stl(handler, namespace, mode='html')
