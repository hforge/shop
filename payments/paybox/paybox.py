# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import String, Decimal, Integer
from itools.gettext import MSG
from itools.i18n import format_datetime

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from enumerates import PayboxStatus
from paybox_views import Paybox_Configure, Paybox_Pay, Paybox_View
from paybox_views import Paybox_End, Paybox_ConfirmPayment
from shop.datatypes import StringFixSize
from shop.payments.payment_way import PaymentWay
from shop.payments.enumerates import PaymentSuccessState


class PayboxBaseTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, is_indexed=True),
        'id_payment': Integer,
        'success': PaymentSuccessState,
        'transaction': String,
        'autorisation': String,
        'state': PayboxStatus(default=PayboxStatus.default),
        'amount': Decimal,
        }



class PayboxTable(Table):

    class_id = 'paybox-payments'
    class_title = MSG(u'Paybox payment Module')
    class_handler = PayboxBaseTable

    view = Paybox_View()


    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        SelectWidget('success', title=MSG(u'Payment ok')),
        TextWidget('transaction', title=MSG(u'Id transaction')),
        TextWidget('autorisation', title=MSG(u'Id Autorisation')),
        SelectWidget('state', title=MSG(u'State')),
        TextWidget('amount', title=MSG(u'Amount')),
        ]


    def get_record_namespace(self, context, record):
        ns = {}
        # Id
        ns['id'] = record.id
        # Complete id
        resource = context.resource
        ns['complete_id'] = 'paybox-%s' % record.id
        # Base namespace
        for key in self.handler.record_schema.keys():
            ns[key] = self.handler.get_record_value(record, key)
        # State
        ns['state'] = PayboxStatus.get_value(ns['state'])
        # Ns success
        ns['success'] = PaymentSuccessState.get_value(ns['success'])
        # HTML
        ns['html'] = None
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        ns['ts'] = format_datetime(value,  accept)
        return ns



class Paybox(PaymentWay):

    class_id = 'paybox'
    class_title = MSG(u'Paybox payment Module')
    class_description = MSG(u'Secured payment paybox')

    # Views
    class_views = ['configure', 'payments']

    logo = '/ui/shop/payments/paybox/images/logo.png'

    # Views
    configure = Paybox_Configure()
    confirm_payment = Paybox_ConfirmPayment()
    end = Paybox_End()

    # Schema
    base_schema = {'PBX_SITE': StringFixSize(size=7),
                   'PBX_RANG': StringFixSize(size=2),
                   'PBX_IDENTIFIANT': String,
                   'PBX_DIFF': StringFixSize(size=2)}

    @classmethod
    def get_metadata_schema(cls):
        schema = PaymentWay.get_metadata_schema()
        # Paybox account configuration
        schema.update(cls.base_schema)
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        PaymentWay._make_resource(cls, folder, name, *args, **kw)
        # Add paybox table
        PayboxTable._make_resource(PayboxTable, folder, '%s/payments' % name)


    def get_namespace_payments(self, context):
        namespace = []
        payments = self.get_resource('payments')
        for record in payments.handler.get_records():
            kw = payments.get_record_namespace(context, record)
            kw['payment_mode'] = self.get_title()
            namespace.append(kw)
        return namespace


    def _show_payment_form(self, context, payment):
        # Add payment in history
        payments = self.get_resource('payments').handler
        payments.add_record({'ref': payment['id'],
                             'amount': payment['total_price']})
        # Show payment form
        return Paybox_Pay().GET(self, context, payment)



register_resource_class(Paybox)
register_resource_class(PayboxTable)
