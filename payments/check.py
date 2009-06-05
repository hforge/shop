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
from itools.csv import Table as BaseTable
from itools.datatypes import Enumerate, String, Decimal, Integer, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime

# Import from ikaaro
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop.payments
from payment_way import PaymentWay
from check_views import CheckPayment_Pay, CheckPayment_Configure

class CheckStates(Enumerate):

    default = 'wait'

    options = [
      {'name': 'wait',     'value': MSG(u'Waiting for your check')},
      {'name': 'received', 'value': MSG(u'Check received')},
      {'name': 'valid',    'value': MSG(u'Payment successful')},
      {'name': 'refused',  'value': MSG(u'Check refused')},
      ]


class CheckPaymentBaseTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, is_indexed=True),
        'amount': Decimal,
        'check_number': Integer,
        'state': CheckStates(default=CheckStates.default),
        }


class CheckPaymentTable(Table):

    class_id = 'checkpayment-payments'
    class_title = MSG(u'Check payment Module')
    class_handler = CheckPaymentBaseTable

    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        TextWidget('amount', title=MSG(u'Amount')),
        TextWidget('check_number', title=MSG(u'Check number')),
        SelectWidget('state', title=MSG(u'State'))
        ]


    def get_record_namespace(self, context, record):
        ns = {}
        # Id
        ns['id'] = record.id
        # Complete id
        resource = context.resource
        complete_id = 'check-%s' % record.id
        uri = '%s/;view_payment?id=%s' % (resource.get_pathto(self), record.id)
        ns['complete_id'] = (complete_id, uri)
        # Base namespace
        for key in self.handler.record_schema.keys():
            ns[key] = self.handler.get_record_value(record, key)
        # Ns success
        ns['success'] = 'XXX'
        ns['state'] = CheckStates.get_value(ns['state'])
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        ns['ts'] = format_datetime(value,  accept)
        return ns



class CheckPayment(PaymentWay):

    class_id = 'check-payment'
    class_title = MSG(u'Payment by check')
    class_description = MSG(u'Payment by check')

    # XXX found a good logo
    logo = '/ui/shop/payments/paybox/images/logo.png'

    # Views
    class_views = ['view', 'configure']

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


    def get_namespace_payments(self, context):
        namespace = []
        payments = self.get_resource('payments')
        for record in payments.handler.get_records():
            kw = payments.get_record_namespace(context, record)
            kw['payment_mode'] = self.get_title()
            namespace.append(kw)
        return namespace


    def _show_payment_form(self, context, payment):
        # Add a record in payments
        payments = self.get_resource('payments')
        payments.handler.add_record({'ref': payment['id'],
                                     'amount': payment['total_price']})
        # Show payment form
        return CheckPayment_Pay().GET(self, context, payment)



register_resource_class(CheckPayment)
register_resource_class(CheckPaymentTable)
