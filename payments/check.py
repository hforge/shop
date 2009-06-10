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
from itools.datatypes import Enumerate, Integer, Unicode
from itools.gettext import MSG
from itools.stl import stl

# Import from ikaaro
from ikaaro.forms import TextWidget, SelectWidget, stl_namespaces
from ikaaro.registry import register_resource_class

# Import from shop.payments
from payment_way import PaymentWay, PaymentWayBaseTable, PaymentWayTable
from check_views import CheckPayment_Pay, CheckPayment_Configure
from check_views import CheckPayment_Manage, Check_RecordOrderView


class CheckStates(Enumerate):

    default = 'wait'

    options = [
      {'name': 'wait',     'value': MSG(u'Waiting for your check')},
      {'name': 'received', 'value': MSG(u'Check received')},
      {'name': 'refused',  'value': MSG(u'Check refused')},
      {'name': 'success',  'value': MSG(u'Payment successful')},
      {'name': 'invalid',  'value': MSG(u'Invalid amount')},
      ]


class CheckPaymentBaseTable(PaymentWayBaseTable):

    record_schema = merge_dicts(
        PaymentWayBaseTable.record_schema,
        check_number=Integer,
        bank=Unicode,
        account_holder=Unicode,
        advance_state=CheckStates)


class CheckPaymentTable(PaymentWayTable):

    class_id = 'checkpayment-payments'
    class_title = MSG(u'Check payment Module')
    class_handler = CheckPaymentBaseTable

    class_views = ['view', 'add_record']

    edit_record = CheckPayment_Manage()

    form = PaymentWayTable.form + [
        TextWidget('check_number', title=MSG(u'Check number')),
        TextWidget('bank', title=MSG(u'Bank')),
        TextWidget('account_holder', title=MSG(u'Account holder')),
        SelectWidget('advance_state', title=MSG(u'Advance state'))
        ]


    record_order_view = Check_RecordOrderView

    def get_record_namespace(self, context, record):
        namespace = PaymentWayTable.get_record_namespace(self, context, record)
        # Advance State
        advance_state = self.handler.get_record_value(record, 'advance_state')
        namespace['advance_state'] = CheckStates.get_value(advance_state)
        return namespace



class CheckPayment(PaymentWay):

    class_id = 'check-payment'
    class_title = MSG(u'Payment by check')
    class_description = MSG(u'Payment by check')

    # XXX found a good logo
    logo = '/ui/shop/payments/paybox/images/logo.png'

    # Views
    class_views = ['configure', 'payments']

    # Views
    configure = CheckPayment_Configure()

    # Schema
    base_schema = {'to': Unicode,
                   'address': Unicode}

    @classmethod
    def get_metadata_schema(cls):
        schema = PaymentWay.get_metadata_schema()
        schema.update(cls.base_schema)
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        PaymentWay._make_resource(cls, folder, name, *args, **kw)
        CheckPaymentTable._make_resource(CheckPaymentTable, folder,
            '%s/payments' % name)


    def _show_payment_form(self, context, payment):
        # Add a record in payments
        payments = self.get_resource('payments')
        payments.handler.add_record({'ref': payment['ref'],
                                     'amount': payment['amount'],
                                     'user': context.user.name})
        # Show payment form
        return CheckPayment_Pay().GET(self, context, payment)



register_resource_class(CheckPayment)
register_resource_class(CheckPaymentTable)
