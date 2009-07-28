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
from itools.datatypes import Boolean, Integer, Unicode
from itools.datatypes import PathDataType, String
from itools.gettext import MSG
from itools.web import STLView, STLForm

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import TextWidget, BooleanCheckBox
from ikaaro.forms import ImageSelectorWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.resource_views import DBResource_Edit

# Import from shop
from datatypes import RIB, IBAN


class TransferPayment_RecordView(STLView):

    template = '/ui/shop/payments/transfer/record_view.xml'

    def get_namespace(self, resource, context):
        get_record_value = self.payment_table.get_record_value
        return {'amount': get_record_value(self.record, 'amount'),
                'ref': get_record_value(self.record, 'ref'),
                'RIB': self.payment_way.get_property('RIB'),
                'IBAN': self.payment_way.get_property('IBAN')}



class TransferPayment_RecordEdit(STLForm):

    template = '/ui/shop/payments/transfer/record_edit.xml'

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
        self.payment_table.update_record(self.id_payment, **kw)
        context.message = MSG_CHANGES_SAVED




class TransferPayment_Configure(DBResource_Edit):

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



class TransferPayment_Pay(STLView):

    access = "is_authenticated"

    template = '/ui/shop/payments/transfer/pay.xml'

    def get_namespace(self, resource, context):
        return {
            'RIB': resource.get_property('RIB'),
            'IBAN': resource.get_property('IBAN'),
            'ref': self.conf['ref'],
            'amount': self.conf['amount']}