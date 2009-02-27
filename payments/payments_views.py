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
from itools.datatypes import Boolean, Integer, Unicode, String
from itools.gettext import MSG
from itools.web import STLView

# Import from ikaaro
from ikaaro import messages
from ikaaro.forms import AutoForm, BooleanRadio, SelectWidget
from ikaaro.views import BrowseForm, CompositeForm

# Import from shop
from enumerates import PaymentWayList


class Payments_Top_View(STLView):

    template = '/ui/payments/top_view.xml'

    access = 'is_admin'

    def get_namespace(self, resource, context):
        ns = {}
        # Payments modes
        payments_modes = resource.get_property('payments_modes')
        ns['payments_modes'] = None
        if payments_modes:
            ns['payments_modes'] = PaymentWayList.get_namespace(payments_modes)
        # Other informations
        for key in ['enabled']:
            ns[key] = resource.get_property(key)
        return ns



class Payments_History_View(BrowseForm):
    """
    View that list history payments.
    """

    title = MSG(u'View')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment.")
    batch_msg2 = MSG(u"There are ${n} payments.")


    table_columns = [
        ('complete_id', MSG(u'Id')),
        ('ts', MSG(u'Date')),
        ('payment_mode', MSG(u'Payment mode')),
        ('success', MSG(u'Success')),
        ('amount', MSG(u'Amount')),
        ]

    def get_items(self, resource, context):
        """ Here we concatanate payments off all payment's mode """
        from payments import PaymentWay
        items = []
        for payment_way in resource.search_resources(cls=PaymentWay):
            payment_mode = payment_way.name
            payment_mode_title = PaymentWayList.get_value(payment_mode)
            for record in payment_way.handler.get_records():
                kw = payment_way.get_record_namespace(context, record)
                kw['payment_mode'] = payment_mode_title
                items.append(kw)
        return items


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        return item[column]



class Payments_View(CompositeForm):

    access = 'is_admin'

    title = MSG(u'View')

    subviews = [
        Payments_Top_View(),
        Payments_History_View(),
    ]



class Payments_Configure(AutoForm):

    access = 'is_admin'

    title = MSG(u'Configure')

    widgets = [
        BooleanRadio('enabled', title=MSG(u'Payments in real mode')),
        SelectWidget('payments_modes', title=MSG(u'Authorized payments mode')),
        ]

    schema = {
        'payments_modes': PaymentWayList(multiple=True, mandatory=True),
        'enabled': Boolean(mandatory=True),
    }


    def get_value(self, resource, context, name, datatype):
        return resource.get_property(name)


    def action(self, resource, context, form):
        # Save configuration
        for key in ['payments_modes', 'enabled']:
            resource.set_property(key, form[key])
        # We activate new payments mode
        resource.activate_payments_modes(form['payments_modes'])
        # Come back
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')



class Payments_End(STLView):
    """The customer is redirect on this page after payment"""

    access = True

    template = '/ui/payments/payments_end.xml'

    query_schema = {'state': Unicode,
                    'ref': String}


    def get_namespace(self, resource, context):
        return context.query
