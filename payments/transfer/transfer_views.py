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
from itools.datatypes import Boolean, Enumerate, Integer, Unicode
from itools.datatypes import PathDataType
from itools.gettext import MSG
from itools.web import STLView, STLForm
from itools.stl import stl
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import MultilineWidget, TextWidget, BooleanCheckBox
from ikaaro.forms import ImageSelectorWidget
from ikaaro.resource_views import DBResource_Edit

# Import from shop
from datatypes import RIB, IBAN
from shop.shop_utils_views import Shop_Progress, Shop_PluginWay_Form

#
#class CheckPayment_RecordAdd(STLForm):
#
#    template = '/ui/shop/payments/check_payment_record_edit.xml'
#
#    schema = {'check_number': Integer,
#              'bank': Unicode,
#              'account_holder': Unicode,
#              'advance_state': CheckStates(mandatory=True)}
#
#
#    def get_namespace(self, resource, context):
#        return self.build_namespace(resource, context)
#
#
#    def add_payment(self, order, payment_way, context, form):
#        kw = form
#        kw['ref'] = order.name
#        if form['advance_state'] == 'success':
#            kw['state'] = True
#            order.set_as_payed(context)
#        else:
#            kw['state'] = False
#            order.set_as_not_payed(context)
#        history = payment_way.get_resource('payments')
#        history.handler.add_record(kw)
#        msg = MSG(u'Changes ok')
#        return context.come_back(msg)
#
#
#class CheckPayment_RecordView(Shop_PluginWay_Form):
#
#    template = '/ui/shop/payments/check_record_order_view.xml'
#
#    def get_namespace(self, order, payment_way, record, context):
#        namespace = {'ref': order.name,
#                     'amount': order.get_property('total_price'),
#                     'to': payment_way.get_property('to'),
#                     'address': payment_way.get_property('address')}
#        return namespace
#
#
#
#class CheckPayment_RecordEdit(Shop_PluginWay_Form):
#
#    template = '/ui/shop/payments/check_record_order_edit.xml'
#
#    def get_namespace(self, order, payment_way, record, context):
#        namespace = {}
#        get_val = payment_way.get_resource('payments').handler.get_record_value
#        for key in ['amount', 'check_number', 'bank', 'account_holder']:
#            namespace[key] = get_val(record, key)
#        advance_state = get_val(record, 'advance_state')
#        namespace['advance_state'] = CheckStates.get_value(advance_state)
#        return namespace



class TransfertPayment_Configure(DBResource_Edit):

    title = MSG(u'Configure')
    access = 'is_admin'

    schema = {'enabled': Boolean(mandatory=True),
              'title': Unicode(mandatory=True),
              'logo': PathDataType(mandatory=True),
              'RIB': RIB(mandatory=True),
              'IBAN': IBAN(mandatory=True)}


    widgets = [
        BooleanCheckBox('enabled', title=MSG(u'Enabled ?')),
        TextWidget('title', title=MSG(u'Title')),
        ImageSelectorWidget('logo',  title=MSG(u'Logo')),
        TextWidget('RIB', title=MSG(u'RIB')),
        TextWidget('IBAN', title=MSG(u'IBAN'))]

    submit_value = MSG(u'Edit configuration')


    def action(self, resource, context, form):
        for key in self.schema.keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')


class TransfertPayment_Pay(STLView):

    access = "is_authenticated"

    template = '/ui/shop/payments/transfert/transferpayment_pay.xml'

    def get_namespace(self, resource, context):
        return {
            'RIB': resource.get_property('RIB'),
            'IBAN': resource.get_property('IBAN'),
            'ref': self.conf['ref'],
            'amount': self.conf['amount']}

