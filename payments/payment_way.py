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
from ikaaro.forms import TextWidget, BooleanCheckBox, XHTMLBody
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from payment_way_views import PaymentWay_RecordView, PaymentWay_Configure
from shop.folder import ShopFolder
from shop.datatypes import UserGroup_Enumerate
from shop.utils import CurrentFolder_AddImage


class PaymentWayBaseTable(BaseTable):

    record_properties = {
        'ref': String(is_indexed=True, is_stored=True),
        'user': String(is_indexed=True),
        'state': Boolean(is_indexed=True),
        'amount': Decimal,
        'resource_validator': String,
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
        TextWidget('resource_validator', title=MSG(u'Resource validator')),
        TextWidget('description', title=MSG(u'Description'))]

    # Views
    add_record = None
    edit_record = None


    def get_record_namespace(self, context, record):
        get_value = self.handler.get_record_value
        namespace = {'id': record.id,
                     'complete_id': '%s-%s' % (self.parent.name, record.id),
                     'payment_mode': self.parent.name}
        # Base namespace
        for key in self.handler.record_properties.keys():
            namespace[key] = get_value(record, key)
        # Amount
        namespace['amount'] = '%s €' % get_value(record, 'amount')
        # User
        users = context.root.get_resource('users')
        username = get_value(record, 'user') or '0'
        user = users.get_resource(username)
        namespace['username'] = username
        namespace['user_title'] = user.get_title()
        namespace['user_email'] = user.get_property('email')
        # State
        namespace['advance_state'] = None
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        namespace['ts'] = format_datetime(value,  accept)
        return namespace


class PaymentWay(ShopFolder):

    class_id = 'payment_way'
    class_views = ['configure', 'payments']

    configure = PaymentWay_Configure()
    add_image = CurrentFolder_AddImage()

    logo = None
    payment_table = PaymentWayTable

    # Backoffice views
    order_view = PaymentWay_RecordView
    order_edit_view = PaymentWay_RecordView

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           data=XHTMLBody(multilingual=True),
                           title=Unicode(multilingual=True),
                           enabled=Boolean(default=True),
                           only_this_groups=UserGroup_Enumerate(multiple=True),
                           logo=PathDataType(multilingual=True))


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create resource
        kw['title'] = {'en': cls.class_title.gettext()}
        kw['description'] = {'en': cls.class_description.gettext()}
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        cls.payment_table._make_resource(cls.payment_table, folder,
            '%s/payments' % name)


    def _get_catalog_values(self):
        # XXX We do not index data from data
        return ShopFolder._get_catalog_values(self)


    def _show_payment_form(self, context, payment):
        # By default we redirect on payment end
        link = '%s/;end?ref=%s' % (context.get_link(self), payment['ref'])
        return context.uri.resolve(link)

    ###################################################
    # Public API
    ###################################################

    def set_payment_as_ok(self, id_record, context):
        """ Overridable: for example to send a custom mail ..."""
        self.parent.set_payment_as_ok(self, id_record, context)


    def create_payment(self, context, payment):
        """ We add payment in payments table. Overridable:
        For example to auto-validate payment or to add additional informations
        """
        payments = self.get_resource('payments').handler
        record = payments.add_record(
            {'ref': payment['ref'],
             'amount': payment['amount'],
             'user': context.user.name,
             'resource_validator': payment['resource_validator']})
        return record


    def get_payment_way_description(self, context, total_amount):
        """ Overridable: for example to add available points... """
        return self.get_property('data')


    def is_enabled(self, context):
        """ Overridable: A payment way can be disabled according to context"""
        return  self.get_property('enabled')


register_resource_class(PaymentWay)
register_resource_class(PaymentWayTable)
