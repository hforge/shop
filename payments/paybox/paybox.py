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
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from enumerates import PayboxStatus
from paybox_views import Paybox_Configure, Paybox_Pay, Paybox_View
from paybox_views import Paybox_ViewPayment, Paybox_End, Paybox_ConfirmPayment
from shop.datatypes import StringFixSize
from shop.payments.payments import PaymentWay
from shop.payments.enumerates import PaymentSuccessState


class PayboxTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, index='keyword'),
        'id_payment': Integer,
        'success': PaymentSuccessState,
        'transaction': String,
        'autorisation': String,
        'status': PayboxStatus,
        'amount': Decimal,
        }




class Paybox(PaymentWay, Table):

    class_id = 'paybox'
    class_title = MSG(u'Paybox payment Module')
    class_handler = PayboxTable

    # Views
    class_views = ['view', 'configure']

    view = Paybox_View()
    view_payment = Paybox_ViewPayment()
    configure = Paybox_Configure()
    confirm_payment = Paybox_ConfirmPayment()
    end = Paybox_End()


    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        SelectWidget('success', title=MSG(u'Payment ok')),
        TextWidget('transaction', title=MSG(u'Id transaction')),
        TextWidget('autorisation', title=MSG(u'Id Autorisation')),
        SelectWidget('status', title=MSG(u'Status')),
        TextWidget('amount', title=MSG(u'Amount')),
        ]


    base_schema = {'PBX_SITE': StringFixSize(size=7),
                   'PBX_RANG': StringFixSize(size=2),
                   'PBX_IDENTIFIANT': String,
                   'PBX_DIFF': StringFixSize(size=2)}


    @classmethod
    def get_metadata_schema(cls):
        schema = Table.get_metadata_schema()
        # Paybox account configuration
        schema.update(cls.base_schema)
        return schema


    def get_record_namespace(self, context, record):
        ns = {}
        # Id
        ns['id'] = record.id
        # Complete id
        resource = context.resource
        complete_id = 'paybox-%s' % record.id
        uri = '%s/;view_payment?id=%s' % (resource.get_pathto(self), record.id)
        ns['complete_id'] = (complete_id, uri)
        # Base namespace
        for key in self.handler.record_schema.keys():
            ns[key] = self.handler.get_record_value(record, key)
        # Amount
        ns['amount'] = '%s €' % ns['amount']
        # Ns success
        ns['success'] = PaymentSuccessState.get_value(ns['success'])
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        ns['ts'] = format_datetime(value,  accept)
        return ns


    def _show_payment_form(self, context, payment):
        return Paybox_Pay().GET(self, context, payment)


register_resource_class(Paybox)
