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

# Import from standard library
from operator import itemgetter

# Import from itools
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from payments
from payments_views import Payments_View, Payments_History_View
from payments_views import Payments_ViewPayment, Payments_EditPayment

# Import from shop
from payment_way import PaymentWay
from shop.utils import ShopFolder
from registry import payment_ways_registry


class Payments(ShopFolder):

    class_id = 'payments'
    class_title = MSG(u'Payment Module')
    class_views = ['history', 'view']

    # Views
    view = Payments_View()
    history = Payments_History_View()

    view_payment = Payments_ViewPayment()
    edit_payment = Payments_EditPayment()


    def get_document_types(self):
        return payment_ways_registry.values()


    ######################
    # Public API
    ######################

    def get_payments_items(self, context, ref=None):
        items = []
        for payment_way, record in self.get_payments_records(context, ref):
            payments = payment_way.get_resource('payments')
            items.append(payments.get_record_namespace(context, record))
        return items


    def get_payments_records(self, context, ref=None):
        records = []
        for payment_way in self.search_resources(cls=PaymentWay):
            payments = payment_way.get_resource('payments')
            if ref:
                for record in payments.handler.search(ref=ref):
                    ts = payments.handler.get_record_value(record, 'ts')
                    records.append((payment_way, record, ts))
            else:
                for record in payments.handler.get_records():
                    records.append((payment_way, record))
        if ref:
            records.sort(key=itemgetter(2))
            records.reverse()
            records = [(x, y) for x, y, z in records]
        return records


    def show_payment_form(self, context, payment):
        """
           payment must be a dictionnary with order's identifiant
           and order price.
           For example:
           payment = {'ref': 'A250',
                      'amount': 250,
                      'mode': 'paybox'}
        """
        # We check that payment dictionnary is correctly fill.
        for key in ['ref', 'amount', 'mode']:
            if key not in payment:
                raise ValueError, u'Invalid order'
        # We check mode is valid and active
        payment_way = self.get_resource(payment['mode'])
        # Check if enabled
        if not payment_way.get_property('enabled'):
            raise ValueError, u'Invalid payment mode (not enabled)'
        # Add payment in history
        payments = payment_way.get_resource('payments').handler
        payments.add_record({'ref': payment['ref'],
                             'amount': payment['amount'],
                             'user': context.user.name})
        # All is ok: We show the payment form
        return payment_way._show_payment_form(context, payment)


register_resource_class(Payments)
