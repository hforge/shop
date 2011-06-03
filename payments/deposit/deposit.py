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
from itools.core import merge_dicts
from itools.gettext import MSG
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from shop
from deposit_views import Deposit_Configure, deposit_schema
from shop.payments.payment_way import PaymentWay
from shop.payments.registry import register_payment_way
from shop.utils import format_price


class Deposit(PaymentWay):

    class_id = 'deposit'
    class_title = MSG(u'Deposit payment module')
    class_description = MSG(u'Deposit payment module')
    class_views = ['configure']

    # Views
    configure = Deposit_Configure()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(PaymentWay.get_metadata_schema(),
                           deposit_schema)


    def _show_payment_form(self, context, payment):
        percent = self.get_property('percent')
        payment['mode'] = 'paybox' # XXX (Can have another name ?)
        if self.get_property('pay_tax'):
            payment['amount'] = payment['amount'] * (percent / decimal('100.0'))
        else:
            payment['amount'] = payment['amount_without_tax'] * (percent / decimal('100.0'))
        return self.parent.show_payment_form(context, payment)


    def get_payment_way_description(self, context, total_amount):
        msg = MSG(u"Pay {percent}% of {original_amount} now ({amount})")
        percent = self.get_property('percent')
        if self.get_property('pay_tax'):
            total_amount = decimal(total_amount['with_tax'])
        else:
            total_amount = decimal(total_amount['without_tax'])
        amount = total_amount * (percent / decimal('100.0'))
        msg = msg.gettext(percent=percent,
                          original_amount=format_price(total_amount),
                          amount=format_price(amount))
        return list(XMLParser(msg.encode('utf-8'))) + self.get_property('data')



register_resource_class(Deposit)
register_payment_way(Deposit)
