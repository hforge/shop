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

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, Enumerate, Unicode
from itools.gettext import MSG
from itools.web import STLForm
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import MultilineWidget
from ikaaro.forms import stl_namespaces
from ikaaro.registry import register_resource_class

# Import from shop.shipping
from shipping_way import ShippingWay, ShippingWayBaseTable, ShippingWayTable
from shop.shop_utils_views import Shop_PluginWay_Form


class Withdrawal_RecordView(Shop_PluginWay_Form):

    template = '/ui/shop/shipping/withdrawal_record_order_view.xml'

    def get_namespace(self, order, shipping_way, record, context):
        return Shop_PluginWay_Form().get_namespace(shipping_way, context)



class Withdrawal_RecordEdit(Shop_PluginWay_Form):

    # XXX TODO: allow to take RDV
    template = '/ui/shop/shipping/withdrawal_record_order_view.xml'

    def get_namespace(self, order, shipping_way, record, context):
        return Shop_PluginWay_Form().get_namespace(shipping_way, context)



class Withdrawal_RecordAdd(STLForm):

    access = 'is_admin'
    template = '/ui/shop/shipping/withdrawal_record_order_add.xml'

    schema = {'state': Boolean}

    def get_namespace(self, resource, context):
        return {'name': resource.name}


    def add_shipping(self, order, shipping_way, context, form):
        order.set_as_sent(context)
        kw = {'ref': order.name,
              'state': 'sent'}
        history = shipping_way.get_resource('history')
        history.handler.add_record(kw)
        msg = MSG(u'Modifications ok')
        return context.come_back(msg)



class WithdrawalStates(Enumerate):

    options = [
      {'name': 'appointment',    'value': MSG(u'Waiting for an appointment')},
      {'name': 'appointment_ok', 'value': MSG(u'Appointment taken')},
      {'name': 'end', 'value': MSG(u'End')} ]


class WithdrawalBaseTable(ShippingWayBaseTable):

    record_properties = merge_dicts(
        ShippingWayBaseTable.record_properties,
        description=Unicode)



class WithdrawalTable(ShippingWayTable):

    class_id = 'withdrawal-table'
    class_title = MSG(u'Withdrawal')
    class_handler = WithdrawalBaseTable

    form = ShippingWayTable.form + [
        MultilineWidget('description', title=MSG(u'Description')) ]

    def get_record_namespace(self, context, record):
        ns = ShippingWayTable.get_record_namespace(self, context, record)
        ns['state'] = WithdrawalStates.get_value(ns['state'])
        return ns



class Withdrawal(ShippingWay):
    """Withdrawal to the store.
    """
    class_id = 'withdrawal'
    class_title = MSG(u'Withdrawal')
    class_version = '20090910'
    class_description = MSG(u'Withdrawal at the store')

    img = '../ui/shop/images/noship.png'

    html_form = list(XMLParser("""
        <form method="POST">
          <button type="submit" class="button" id="button-order">Ok</button>
          <input type="hidden" name="shipping" value="${name}"/>
        </form>
        """,
        stl_namespaces))

    shipping_history_cls = WithdrawalTable

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        kw['title'] = {'en': cls.class_title.gettext()}
        kw['description'] = {'en': cls.class_description.gettext()}
        kw['is_free'] = True
        ShippingWay._make_resource(cls, folder, name, *args, **kw)


    # Admin views
    order_view = Withdrawal_RecordView()
    order_add_view = Withdrawal_RecordAdd()
    order_edit_view = Withdrawal_RecordEdit()


    def update_20090910(self):
        self.set_property('is_free', True)


register_resource_class(Withdrawal)
register_resource_class(WithdrawalTable)
