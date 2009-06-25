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
from itools.datatypes import Enumerate, Integer, Unicode
from itools.gettext import MSG
from itools.web import STLView, STLForm
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import MultilineWidget, TextWidget
from ikaaro.resource_views import DBResource_Edit

# Import from shop
from shop.shop_utils_views import Shop_Progress



class CheckStates(Enumerate):

    default = 'wait'

    options = [
      {'name': 'refused',  'value': MSG(u'Check refused by the bank')},
      {'name': 'invalid',  'value': MSG(u'Invalid amount')},
      {'name': 'success',  'value': MSG(u'Payment successful')},
      ]



class CheckPayment_Pay(STLView):

    access = "is_authenticated"

    template = '/ui/shop/payments/checkpayment_pay.xml'

    conf = None

    def GET(self, resource, context, conf):
        self.conf = conf
        return STLView.GET(self, resource, context)


    def get_namespace(self, resource, context):
        namespace = {
            'to': resource.get_property('to'),
            'progress': Shop_Progress(index=6).GET(resource, context),
            'ref': self.conf['ref'],
            'amount': self.conf['amount']}
        address = resource.get_property('address').encode('utf-8')
        namespace['address'] = XMLParser(address.replace('\n', '<br/>'))
        return namespace



class CheckPayment_RecordAdd(STLForm):

    template = '/ui/shop/payments/check_payment_record_edit.xml'

    schema = {'check_number': Integer,
              'bank': Unicode,
              'account_holder': Unicode,
              'advance_state': CheckStates(mandatory=True)}


    def get_namespace(self, resource, context):
        return self.build_namespace(resource, context)


    def add_payment(self, order, payment_way, context, form):
        kw = form
        kw['ref'] = order.name
        if form['advance_state'] == 'success':
            kw['state'] = True
            order.set_as_payed()
        else:
            kw['state'] = False
            order.set_as_not_payed()
        history = payment_way.get_resource('payments')
        history.handler.add_record(kw)
        msg = MSG(u'Changes ok')
        return context.come_back(msg)


class CheckPayment_RecordView(STLForm):

    template = '/ui/shop/payments/check_record_order_view.xml'

    def get_namespace(self, resource, context):
        order = context.resource
        namespace = {'ref': order.name,
                     'amount': 'XXX',
                     'to': resource.parent.get_property('to'),
                     'address': resource.parent.get_property('address')}
        return namespace



class CheckPayment_RecordEdit(STLForm):

    template = '/ui/shop/payments/check_record_order_edit.xml'

    def GET(self, order, payment_way, record, context):
        # Get the template
        template = self.get_template(order, context)
        # Get the namespace
        namespace = self.get_namespace(order, payment_way, record, context)
        # Ok
        from itools.stl import stl
        return stl(template, namespace)


    def get_namespace(self, order, payment_way, record, context):
        namespace = {}
        get_val = payment_way.get_resource('payments').handler.get_record_value
        for key in ['amount', 'check_number', 'bank', 'account_holder']:
            namespace[key] = get_val(record, key)
        advance_state = get_val(record, 'advance_state')
        namespace['advance_state'] = CheckStates.get_value(advance_state)
        return namespace



class CheckPayment_Configure(DBResource_Edit):

    title = MSG(u'Configure CheckPayment module')
    access = 'is_admin'

    schema = {'to': Unicode,
              'address': Unicode}


    widgets = [
        TextWidget('to', title=MSG(u"A l'ordre de")),
        MultilineWidget('address', title=MSG(u'Address'))]

    submit_value = MSG(u'Edit configuration')


    def action(self, resource, context, form):
        for key in self.schema.keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')
