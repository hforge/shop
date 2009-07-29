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
from itools.datatypes import Boolean, Integer, Unicode
from itools.datatypes import String
from itools.gettext import MSG
from itools.web import STLView, STLForm
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import MultilineWidget
from ikaaro.messages import MSG_CHANGES_SAVED

# Import from shop
from shop.payments.payment_way_views import PaymentWay_Configure



class CashPayment_RecordView(STLView):

    template = '/ui/shop/payments/cash/record_view.xml'

    def get_namespace(self, resource, context):
        get_record_value = self.payment_table.get_record_value
        return {'is_ok': get_record_value(self.record, 'state'),
                'amount': get_record_value(self.record, 'amount'),
                'ref': get_record_value(self.record, 'ref'),
                'address': self.payment_way.get_property('address')}


class CashPayment_RecordEdit(STLForm):

    template = '/ui/shop/payments/cash/record_edit.xml'

    schema = {'payment_way': String,
              'id_payment': Integer,
              'state': Boolean}


    def get_namespace(self, resource, context):
        return self.build_namespace(resource, context)


    def get_value(self, resource, context, name, datatype):
        if name == 'payment_way':
            return self.payment_way.name
        elif name == 'id_payment':
            return self.id_payment
        get_record_value = self.payment_table.get_record_value
        return get_record_value(self.record, name)


    def action_edit_payment(self, resource, context, form):
        kw = {'state': form['state']}
        if kw['state']:
            self.payment_way.set_payment_as_ok(self.id_payment, context)
        self.payment_table.update_record(self.id_payment, **kw)
        context.message = MSG_CHANGES_SAVED



class CashPayment_Configure(PaymentWay_Configure):

    title = MSG(u'Configure checkpayment module')

    schema = merge_dicts(PaymentWay_Configure.schema,
                         address=Unicode(mandatory=True))


    widgets = PaymentWay_Configure.widgets + [
        MultilineWidget('address', title=MSG(u'Address'))]



class CashPayment_Pay(STLView):

    access = "is_authenticated"

    template = '/ui/shop/payments/cash/cashpayment_pay.xml'

    def get_namespace(self, resource, context):
        get = resource.get_property
        address = get('address').encode('utf-8').replace('\n', '<br/>')
        return {
            'address': XMLParser(address),
            'ref': self.conf['ref'],
            'amount': self.conf['amount']}
