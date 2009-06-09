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
from itools.core import merge_dicts
from itools.datatypes import Boolean, String, Decimal, Integer
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class

# Import from shop
from enumerates import PayboxStatus
from paybox_views import Paybox_Configure, Paybox_Pay, Paybox_View
from paybox_views import Paybox_End, Paybox_ConfirmPayment
from shop.datatypes import StringFixSize
from shop.payments.payment_way import PaymentWay, PaymentWayBaseTable
from shop.payments.payment_way import PaymentWayTable


class PayboxBaseTable(PaymentWayBaseTable):

    record_schema = merge_dicts(
        PaymentWayBaseTable.record_schema,
        id_payment=Integer,
        transaction=String,
        autorisation=String,
        advance_state=PayboxStatus)



class PayboxTable(PaymentWayTable):

    class_id = 'paybox-payments'
    class_title = MSG(u'Payment by CB (Paybox)')
    class_handler = PayboxBaseTable

    view = Paybox_View()


    form = PaymentWayTable.form + [
        TextWidget('transaction', title=MSG(u'Id transaction')),
        TextWidget('autorisation', title=MSG(u'Id Autorisation')),
        SelectWidget('advance_state', title=MSG(u'Advance State')),
        ]


    def get_record_namespace(self, context, record):
        namespace = PaymentWayTable.get_record_namespace(self, context, record)
        # Advance state
        advance_state = self.handler.get_record_value(record, 'advance_state')
        namespace['advance_state'] = PayboxStatus.get_value(advance_state)
        return namespace



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
                   'PBX_DIFF': StringFixSize(size=2),
                   'real_mode': Boolean(default=False)}

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
                             'amount': payment['total_price'],
                             'user': context.user.name})
        # Show payment form
        return Paybox_Pay().GET(self, context, payment)



register_resource_class(Paybox)
register_resource_class(PayboxTable)
