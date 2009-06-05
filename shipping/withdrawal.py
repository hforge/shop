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
from itools.csv import Table as BaseTable
from itools.datatypes import Enumerate, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.stl import stl
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget, stl_namespaces
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop.shipping
from shipping_way import ShippingWay


#####################################################
## Withdrawal
#####################################################

class WithdrawalStates(Enumerate):

    options = [
      {'name': 'rdv',      'value': MSG(u'Waiting for a rdv')},
      {'name': 'rdv_take', 'value': MSG(u'RDV Taken')},
      ]


class WithdrawalBaseTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, is_indexed=True),
        'description': Unicode,
        'state': WithdrawalStates
        }



class WithdrawalTable(Table):

    class_id = 'withdrawal-table'
    class_title = MSG(u'Withdrawal')
    class_handler = WithdrawalBaseTable


    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        TextWidget('description', title=MSG(u'Description')),
        SelectWidget('state', title=MSG(u'State'))
        ]


    html_form = list(XMLParser("""
      ${description}
        """,
        stl_namespaces))


    def get_html(self, context, record):
        get_value = self.handler.get_record_value
        namespace = {'description': get_value(record, 'description')}
        return stl(events=self.html_form, namespace=namespace)


    def get_record_namespace(self, context, record):
        ns = {}
        # Id
        ns['id'] = record.id
        # Complete id
        resource = context.resource
        complete_id = 'withdrawal-%s' % record.id
        uri = '%s/;view_payment?id=%s' % (resource.get_pathto(self), record.id)
        ns['complete_id'] = (complete_id, uri)
        # Base namespace
        for key in self.handler.record_schema.keys():
            ns[key] = self.handler.get_record_value(record, key)
        # State
        ns['state'] = WithdrawalStates.get_value(ns['state'])
        # Html
        ns['html'] = self.get_html(context, record)
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        ns['ts'] = format_datetime(value,  accept)
        return ns



class Withdrawal(ShippingWay):

    class_id = 'withdrawal'
    class_title = MSG(u'Withdrawal')

    class_description = MSG(u'Withdrawal to the store.')

    img = '../ui/shop/images/noship.png'

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
