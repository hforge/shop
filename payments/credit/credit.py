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

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop.payments
from shop.datatypes import Users_Enumerate
from shop.payments.payment_way import PaymentWay
from shop.payments.payment_way_views import PaymentWay_Configure
from shop.payments.registry import register_payment_way
from shop.utils import format_price
from credit_views import CreditPayment_View


class CreditAvailable_Basetable(BaseTable):

    record_properties = {
        'user': Users_Enumerate(is_indexed=True),
        'amount': Decimal,
        'description': Unicode}


class CreditAvailable_Table(Table):

    class_id = 'credit-available-table'
    class_handler = CreditAvailable_Basetable
    class_views = ['view', 'back']

    back = GoToSpecificDocument(specific_document='..',
                                title=MSG(u'Back'))

    form = [TextWidget('user', title=MSG(u'User id')),
            TextWidget('amount', title=MSG(u'Credit amount')),
            TextWidget('description', title=MSG(u'Description'))]


class CreditPayment(PaymentWay):

    class_id = 'credit-payment'
    class_title = MSG(u'Credit payment')
    class_views = ['view', 'see_voucher', 'configure']

    view = CreditPayment_View()
    configure = PaymentWay_Configure()
    see_voucher = GoToSpecificDocument(specific_document='users-credit',
                                title=MSG(u'List voucher'))

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


    def get_credit_namespace_available_for_user(self, user_name):
        ns = []
        users_credit = self.get_resource('users-credit').handler
        results = users_credit.search(user=user_name)
        if len(results) == 0:
            return ns
        get_value = users_credit.get_record_value
        for record in results:
            amount = get_value(record, 'amount')
            ns.append({'user': get_value(record, 'user'),
                       'description': get_value(record, 'description'),
                       'amount': format_price(amount)})
        return ns


    def create_payment(self, context, payment):
        # Add the payment by credit
        # XXX We have to check if credit >= amount
        payments = self.get_resource('payments').handler
        amount_available = self.get_credit_available_for_user(context.user.name)
        amount_payed = min(payment['amount'], amount_available)
        record = payments.add_record(
            {'ref': payment['ref'],
             'amount': amount_payed,
             'user': context.user.name,
             'state': True,
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


    def get_payment_way_description(self, context, total_amount):
        total_amount = total_amount['with_tax']
        if not type(total_amount) is decimal:
            # XXX We don't need currency
            total_amount = decimal(total_amount.split(' ')[0])
        amount_available = self.get_credit_available_for_user(context.user.name)
        remaining_amount = amount_available - total_amount
        if remaining_amount < decimal('0'):
            remaining_amount = decimal('0')
        namespace = {'amount_available': format_price(amount_available),
                     'has_to_complete_payment': amount_available < total_amount,
                     'amount_to_pay': format_price(total_amount-amount_available),
                     'remaining_amount': format_price(remaining_amount),
                     'total_amount': format_price(total_amount)}
        description_template = self.get_resource(
            '/ui/backoffice/payments/credit/description.xml')
        return stl(description_template, namespace=namespace)


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
