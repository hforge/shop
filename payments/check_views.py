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
from itools.datatypes import Unicode
from itools.gettext import MSG
from itools.web import STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import MultilineWidget, ReadOnlyWidget, TextWidget
from ikaaro.forms import SelectWidget
from ikaaro.resource_views import DBResource_Edit
from ikaaro.table_views import Table_EditRecord

# Import from shop
from shop.shop_utils_views import Shop_Progress


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



class CheckPayment_Manage(Table_EditRecord):

    widgets = [ReadOnlyWidget('ref', title=MSG(u'Order ref')),
               ReadOnlyWidget('amount', title=MSG(u'Amount')),
               ReadOnlyWidget('user', title=MSG(u'User')),
               TextWidget('check_number', title=MSG(u'Check number')),
               TextWidget('bank', title=MSG(u'Bank')),
               TextWidget('account_holder', title=MSG(u'Account holder')),
               SelectWidget('state', title=MSG(u'State')),
               SelectWidget('advance_state', title=MSG(u'Advance State'))]


    def get_widgets(self, resource, context):
        return self.widgets


    def action_add_or_edit(self, resource, context, record):
        # Add or edit
        Table_EditRecord.action_add_or_edit(self, resource, context, record)
        # Set workflow
        if record['advance_state'] == 'success':
            payments = resource.parent.set_payment_as_ok(context,
                          record['ref'])


class Check_RecordOrderView(STLView):

    template = '/ui/shop/payments/check_record_order_view.xml'

    def get_namespace(self, resource, context):
        record = self.record
        get_value = resource.handler.get_record_value
        namespace = {'is_wait': get_value(record, 'advance_state') == 'wait',
                     'to': resource.parent.get_property('to'),
                     'address': resource.parent.get_property('address')}
        for key in ['ref', 'amount']:
            namespace[key] = get_value(record, key)
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
