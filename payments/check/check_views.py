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
from itools.datatypes import Enumerate, Integer, Unicode, String
from itools.gettext import MSG
from itools.web import STLView, STLForm
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.forms import MultilineWidget, TextWidget

# Import from shop
from shop.payments.payment_way_views import PaymentWay_Configure
from shop.payments.payment_way_views import PaymentWay_EndView


class CheckStates(Enumerate):

    default = 'wait'

    options = [
      {'name': 'refused',  'value': MSG(u'Check refused by the bank')},
      {'name': 'invalid',  'value': MSG(u'Invalid amount')},
      {'name': 'success',  'value': MSG(u'Payment successful')},
      ]



class CheckPayment_End(PaymentWay_EndView):

    access = "is_authenticated"

    template = '/ui/shop/payments/check/end.xml'

    def get_namespace(self, resource, context):
        address = resource.get_property('address').encode('utf-8')
        return merge_dicts(
            PaymentWay_EndView.get_namespace(self, resource, context),
            to=resource.get_property('to'),
            address=XMLParser(address.replace('\n', '<br/>')))



class CheckPayment_RecordView(STLView):

    template = '/ui/shop/payments/check/record_view.xml'

    def get_namespace(self, resource, context):
        get_record_value = self.payment_table.get_record_value
        advance_state = get_record_value(self.record, 'advance_state')
        amount = '%.2f €' % get_record_value(self.record, 'amount')
        return {'amount': amount,
                'is_ok': (advance_state == 'success'),
                'ref': get_record_value(self.record, 'ref'),
                'to': self.payment_way.get_property('to'),
                'address': self.payment_way.get_property('address')}



class CheckPayment_RecordEdit(STLForm):

    template = '/ui/shop/payments/check/record_edit.xml'

    schema = {'payment_way': String,
              'id_payment': Integer,
              'check_number': Integer,
              'bank': Unicode,
              'account_holder': Unicode,
              'advance_state': CheckStates(mandatory=True)}


    def get_value(self, resource, context, name, datatype):
        if name == 'payment_way':
            return self.payment_way.name
        elif name == 'id_payment':
            return self.id_payment
        get_record_value = self.payment_table.get_record_value
        return get_record_value(self.record, name)


    def action_edit_payment(self, resource, context, form):
        kw = {}
        for key in ['check_number', 'bank', 'account_holder', 'advance_state']:
            kw[key] = form[key]
        # Set payment as payed ?
        kw['state'] = form['advance_state'] == 'success'
        if kw['state']:
            self.payment_way.set_payment_as_ok(self.id_payment, context)
        # Update record
        self.payment_table.update_record(self.id_payment, **kw)
        context.message = MSG_CHANGES_SAVED



class CheckPayment_Configure(PaymentWay_Configure):

    title = MSG(u'Configure checkpayment module')

    schema = merge_dicts(PaymentWay_Configure.schema,
                         to=Unicode(mandatory=True),
                         address=Unicode(mandatory=True))


    widgets = PaymentWay_Configure.widgets + [
        TextWidget('to', title=MSG(u"A l'ordre de")),
        MultilineWidget('address', title=MSG(u'Address'))]
