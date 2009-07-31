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
from itools.web import STLView
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.table_views import Table_EditRecord, Table_AddRecord


class Addresses_Book(STLView):

    access = 'is_authenticated'
    title = MSG(u'My address book')
    template = '/ui/shop/addresses_book.xml'

    def get_namespace(self, resource, context):
        namespace = {'addresses': []}
        shop = resource.get_site_root().get_resource('shop')
        addresses = shop.get_resource('addresses').handler
        for record in addresses.search(user=context.user.name):
            ns = {'id': record.id}
            ns.update(shop.get_user_address_namespace(record.id))
            namespace['addresses'].append(ns)
        return namespace


class Addresses_AddAddress(Table_AddRecord):

    access = 'is_authenticated'

    title = MSG(u'Fill a new address')

    def action_add_or_edit(self, resource, context, record):
        # We add current user
        record['user'] = context.user.name
        # Normal action
        Table_AddRecord.action_add_or_edit(self, resource, context, record)


    def action_on_success(self, resource, context):
        return context.come_back(MSG(u'New address added.'),
                                 goto=';addresses_book')



class Addresses_EditAddress(Table_EditRecord):

    access = 'is_authenticated'

    title = MSG(u'Edit address')

    # XXX Sylvain do in ikaaro SECURIY
    # We have to check that user is authorized to edit


    def action_add_or_edit(self, resource, context, record):
        # We add current user
        record['user'] = context.user.name
        # Normal action
        Table_EditRecord.action_add_or_edit(self, resource, context, record)


    def action_on_success(self, resource, context):
        return context.come_back(MSG(u'Address modified'),
                                 goto=';addresses_book')
