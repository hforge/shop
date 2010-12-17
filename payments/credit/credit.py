# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from itools
from itools.csv import Table as BaseTable
from itools.datatypes import Decimal, String, Unicode
from itools.gettext import MSG
from itools.stl import stl
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import stl_namespaces, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop.payments
from shop.payments.payment_way import PaymentWay
from shop.payments.payment_way_views import PaymentWay_Configure
from shop.payments.payments_views import Payments_ChoosePayment
from shop.payments.registry import register_payment_way


class CreditAvailable_Basetable(BaseTable):

    record_properties = {
        'user': String(is_indexed=True),
        'amount': Decimal,
        'description': Unicode}


class CreditAvailable_Table(Table):

    class_id = 'credit-available-table'
    class_handler = CreditAvailable_Basetable

    form = [TextWidget('user', title=MSG(u'User id')),
            TextWidget('amount', title=MSG(u'Credit amount')),
            TextWidget('description', title=MSG(u'Description'))]


class CreditPayment(PaymentWay):

    class_id = 'credit-payment'
    class_title = MSG(u'Credit payment')
    class_views = ['configure', 'payments']

    configure = PaymentWay_Configure()

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create resource
        PaymentWay._make_resource(cls, folder, name, *args, **kw)
        CreditAvailable_Table._make_resource(CreditAvailable_Table, folder,
            '%s/users-credit' % name)


    def get_credit_available_for_user(self, user_name):
        users_credit = self.get_resource('users-credit').handler
        results = users_credit.search(user=user_name)
        if len(results) == 0:
            return decimal('0.0')
        credit = decimal('0.0')
        for record in results:
            credit += users_credit.get_record_value(record, 'amount')
        return credit


    def create_payment(self, context, payment):
        # Add the payment by credit
        # XXX We have to check if credit >= amount
        payments = self.get_resource('payments').handler
        #credit = self.get_credit_available_for_user(context.user)
        record = payments.add_record(
            {'ref': payment['ref'],
             'amount': payment['amount'],
             'user': context.user.name,
             'resource_validator': payment['resource_validator']})
        # The payment is automatically validated
        self.set_payment_as_ok(record.id, context)
        return record


    def is_enabled(self, context):
        if not self.get_property('enabled'):
            return False
        # Only enabled if credit > 0
        amount_available = self.get_credit_available_for_user(context.user.name)
        return amount_available > decimal('0.0')


    description = list(XMLParser("""
         You can choose to pay with the credit available in your account<br/>
         You have <b>${amount_available}€</b> available in your account<br/>
         <stl:block stl:if="has_to_complete_payment">
           So you just have to pay <b>${amount_to_pay}€</b>
           (${total_amount}€ - ${amount_available}€)
         </stl:block>
         <stl:block stl:if="not has_to_complete_payment">
           So you have to pay <b>0€</b>
         </stl:block><br/>
         After this payment, you will have a credit of ${remaining_amount}€.
         """, stl_namespaces))


    def get_payment_way_description(self, context, total_amount):
        total_amount = decimal(total_amount['with_tax'])
        amount_available = self.get_credit_available_for_user(context.user.name)
        remaining_amount = amount_available - total_amount
        if remaining_amount < decimal('0'):
            remaining_amount = decimal('0')
        namespace = {'amount_available': amount_available,
                     'has_to_complete_payment': amount_available < total_amount,
                     'amount_to_pay': total_amount-amount_available,
                     'remaining_amount': remaining_amount,
                     'total_amount': total_amount}
        return stl(events=self.description, namespace=namespace)


    def _show_payment_form(self, context, payment):
        amount_available = self.get_credit_available_for_user(context.user.name)
        remaining_to_pay = payment['amount'] - amount_available
        # Partial payment
        if remaining_to_pay > decimal('0'):
            # Delete credit
            users_credit = self.get_resource('users-credit')
            results = users_credit.handler.search(user=context.user.name)
            if len(results) == 0:
                raise ValueError, 'Error, credit do not exist'
            record = results[0]
            old_amount = users_credit.handler.get_record_value(record, 'amount')
            new_amount = old_amount - payment['amount']
            if new_amount < decimal('0'):
                users_credit.del_record(record.id)
            else:
                kw = {'amount': new_amount}
                users_credit.update_recod(record.id, **kw)
            # Encapsulate in pay view
            payment['mode'] = 'paybox' # XXX (Can have another name ?)
            payment['amount'] = remaining_to_pay
            return self.parent.show_payment_form(context, payment)
        # Complete payment
        return PaymentWay._show_payment_form(self, context, payment)


register_resource_class(CreditPayment)
register_payment_way(CreditPayment)
