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
from itools.csv import CSVFile
from itools.gettext import MSG
from itools.web import BaseView

# Import from shop
from shop.modules import ShopModule


class ShopModule_ExportUsers_View(BaseView):

    access = 'is_admin'


    def GET(self, resource, context):
        search = context.root.search(format='user')
        columns = ['email', 'lastname', 'firstname', 'gender', 'ctime',
                   'last_time', 'phone1', 'phone2']
        csv = CSVFile()
        from shop.user import ShopUser
        dynamic_schema = ShopUser.get_dynamic_schema()
        print dynamic_schema
        for brain in search.get_documents():
            user = context.root.get_resource(brain.abspath)
            row = []
            # Name
            row.append(user.name)
            row.append(str(user.get_property('is_enabled')))
            row.append(user.get_property('user_group'))
            # Base informations
            for column in columns:
                value = user.get_property(column)
                try:
                  row.append(value.encode('utf-8'))
                except:
                    pass
            csv.add_row(row)
        context.set_content_type('text/csv')
        context.set_content_disposition('attachment; filename=export.csv')
        return csv.to_str()




class ShopModule_ExportUsers(ShopModule):

    class_id = 'shop_module_export_users'
    class_title = MSG(u'Export Users')
    class_views = ['view']
    class_description = MSG(u'Export users')

    view = ShopModule_ExportUsers_View()
