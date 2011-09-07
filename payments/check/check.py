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
from itools.datatypes import Integer, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class

# Import from shop.payments
from shop.payments.payment_way import PaymentWay, PaymentWayBaseTable
from shop.payments.payment_way import PaymentWayTable
from shop.payments.registry import register_payment_way
from check_views import CheckPayment_RecordEdit, CheckPayment_End
from check_views import CheckPayment_Configure, CheckStates
from check_views import CheckPayment_RecordView


class CheckPaymentBaseTable(PaymentWayBaseTable):

    record_properties = merge_dicts(
        PaymentWayBaseTable.record_properties,
        check_number=Integer(title=MSG(u'Check number')),
        bank=Unicode(title=MSG(u'Bank')),
        account_holder=Unicode(title=MSG(u'Account holder')),
        advance_state=CheckStates(title=MSG(u'Advance State')))


class CheckPaymentTable(PaymentWayTable):

    class_id = 'checkpayment-payments'
    class_title = MSG(u'Check payment Module')
    class_handler = CheckPaymentBaseTable

    class_views = ['view', 'add_record']

    form = PaymentWayTable.form + [
        TextWidget('check_number', title=MSG(u'Check number')),
        TextWidget('bank', title=MSG(u'Bank')),
        TextWidget('account_holder', title=MSG(u'Account holder')),
        SelectWidget('advance_state', title=MSG(u'Advance state'))
        ]


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
    class_views = ['configure', 'payments']

    # XXX found a good logo
    logo = '/ui/backoffice/payments/paybox/images/logo.png'
    payment_table = CheckPaymentTable

    # Views
    configure = CheckPayment_Configure()
    end = CheckPayment_End()

    # Order admin views
    order_view = CheckPayment_RecordView
    order_edit_view = CheckPayment_RecordEdit

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(PaymentWay.get_metadata_schema(),
                           to=Unicode,
                           address=Unicode)


register_resource_class(CheckPayment)
register_resource_class(CheckPaymentTable)

register_payment_way(CheckPayment)
