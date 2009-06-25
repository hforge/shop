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

# Import from standard library
from decimal import Decimal as decimal

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, Enumerate, String, Unicode
from itools.gettext import MSG
from itools.stl import stl
from itools.web import STLForm, STLView
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget, MultilineWidget
from ikaaro.forms import stl_namespaces
from ikaaro.registry import register_resource_class

# Import from shop.shipping
from shipping_way import ShippingWay, ShippingWayBaseTable, ShippingWayTable


#####################################################
## Withdrawal
#####################################################
class Withdrawal_RecordOrderView(STLView):

    template = '/ui/shop/shipping/withdrawal_record_order_view.xml'


    def get_namespace(self, resource, context):
        record = self.record
        get_value = resource.handler.get_record_value
        return {'description': get_value(record, 'description')}

class Withdrawal_RecordEdit(STLView):

    template = '/ui/shop/shipping/withdrawal_record_order_view.xml'

    def GET(self, order, shipping_way, record, context):
        # Get the template
        template = self.get_template(order, context)
        # Get the namespace
        namespace = self.get_namespace(order, shipping_way, record, context)
        # Ok
        from itools.stl import stl
        return stl(template, namespace)


    def get_namespace(self, order, shipping_way, record, context):
        namespace = {}
        return namespace


class Withdrawal_RecordAdd(STLForm):

    access = 'is_admin'

    template = '/ui/shop/shipping/withdrawal_record_order_add.xml'

    schema = {'state': Boolean}

    def get_namespace(self, resource, context):
        return self.build_namespace(resource, context)


    def add_shipping(self, order, shipping_way, context, form):
        order.set_as_sent()
        kw = {'ref': order.name,
              'state': 'sended'}
        history = shipping_way.get_resource('history')
        history.handler.add_record(kw)
        msg = MSG(u'Modifications ok')
        return context.come_back(msg)



class WithdrawalStates(Enumerate):

    options = [
      {'name': 'appointment',    'value': MSG(u'Waiting for an appointment')},
      {'name': 'appointment_ok', 'value': MSG(u'Appointment taken')},
      {'name': 'end', 'value': MSG(u'End')},
      ]


class WithdrawalBaseTable(ShippingWayBaseTable):

    record_schema = merge_dicts(
        ShippingWayBaseTable.record_schema,
        description=Unicode)



class WithdrawalTable(ShippingWayTable):

    class_id = 'withdrawal-table'
    class_title = MSG(u'Withdrawal')
    class_handler = WithdrawalBaseTable


    form = ShippingWayTable.form + [
        MultilineWidget('description', title=MSG(u'Description')),
        ]


    record_order_view = Withdrawal_RecordOrderView

    def get_record_namespace(self, context, record):
        ns = ShippingWayTable.get_record_namespace(self, context, record)
        ns['state'] = WithdrawalStates.get_value(ns['state'])
        return ns



class Withdrawal(ShippingWay):

    class_id = 'withdrawal'
    class_title = MSG(u'Withdrawal')
    class_description = MSG(u'Withdrawal to the store.')

    img = '../ui/shop/images/noship.png'

    # Admin views
    order_add_view = Withdrawal_RecordAdd()
    order_edit_view = Withdrawal_RecordEdit()

    html_form = list(XMLParser("""
        <form method="POST">
          Withdrawal to the store
          <input type="submit" id="button-order" value="Ok"/>
          <input type="hidden" name="shipping" value="${name}"/>
        </form>
        """,
        stl_namespaces))

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ShippingWay._make_resource(cls, folder, name, *args, **kw)
        WithdrawalTable._make_resource(WithdrawalTable, folder,
            '%s/history' % name)


    def get_price(self, country, purchase_price, purchase_weight):
        return decimal(0)


register_resource_class(Withdrawal)
register_resource_class(WithdrawalTable)
