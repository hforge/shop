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

# Import from itools
from itools.core import merge_dicts
from itools.csv import Table as BaseTable
from itools.datatypes import Boolean, String, Decimal
from itools.datatypes import PathDataType, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime

# Import from ikaaro
from ikaaro.forms import TextWidget, BooleanCheckBox
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.editable import Editable
from shop.utils import ShopFolder


class PaymentWayBaseTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, is_indexed=True),
        'user': String(is_indexed=True),
        'state': Boolean(is_indexed=True),
        'amount': Decimal,
        'description': Unicode}


class PaymentWayTable(Table):

    class_id = 'payment-table'
    class_handler = PaymentWayBaseTable
    class_views = ['view']

    form = [
        TextWidget('ref', title=MSG(u'Payment number')),
        TextWidget('user', title=MSG(u'User id')),
        BooleanCheckBox('state', title=MSG(u'State')),
        TextWidget('amount', title=MSG(u'Amount')),
        TextWidget('description', title=MSG(u'Description'))]

    # Views
    # XXX Sylvain
    # add_record = None
    edit_record = None

    # XXX Sylvain, to delete
    record_order_view = None


    def get_record_namespace(self, context, record):
        get_value = self.handler.get_record_value
        namespace = {'id': record.id,
                     'complete_id': '%s-%s' % (self.parent.name, record.id),
                     'payment_name': self.parent.name}
        # Base namespace
        for key in self.handler.record_schema.keys():
            namespace[key] = get_value(record, key)
        # Amount
        namespace['amount'] = '%s €' % get_value(record, 'amount')
        # User
        users = context.root.get_resource('users')
        user = users.get_resource(get_value(record, 'user') or '0')
        namespace['user_title'] = user.get_title()
        namespace['user_email'] = user.get_property('email')
        # State
        namespace['advance_state'] = None
        # HTML
        if self.record_order_view:
            view = self.record_order_view()
            view.record = record
            namespace['html'] = view.GET(self, context)
        else:
            namespace['html'] = None
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        namespace['ts'] = format_datetime(value,  accept)
        return namespace


class PaymentWay(Editable, ShopFolder):

    class_id = 'payment_way'

    logo = None
    payment_table = PaymentWayTable

    # Backoffice views
    order_edit_view = None

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           Editable.get_metadata_schema(),
                           enabled=Boolean(default=True),
                           logo=PathDataType(multilingual=True))


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create resource
        kw['title'] = {'en': cls.class_title.gettext()}
        kw['description'] = {'en': cls.class_description.gettext()}
        kw['logo'] = cls.logo
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        cls.payment_table._make_resource(cls.payment_table, folder,
            '%s/payments' % name)


    def _get_catalog_values(self):
        # XXX We do not index data from Editable
        return ShopFolder._get_catalog_values(self)



register_resource_class(PaymentWay)
register_resource_class(PaymentWayTable)
