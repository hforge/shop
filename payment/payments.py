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
from itools.csv import Table as BaseTable
from itools.datatypes import String, Boolean, Decimal
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class
from ikaaro.table import Table
from ikaaro.forms import TextWidget, BooleanCheckBox, SelectWidget

# Import from package
from payments_views import Payments_View

#from paybox_views import Paybox_Pay, Paybox_ConfirmPayment, Paybox_View
#from paybox_views import Paybox_Configure, Paybox_PaymentEnd
#from enumerates import Devises, PayboxStatus


class PaymentsTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, index='keyword'),
        'transaction': String,
        'autorisation': String,
        'payment_ok': Boolean,
        'amount': Decimal,
        'status': PayboxStatus,
        'devise': Devises,
        }


class Payments(Table):
    """
    This table contains the history of attempted or successful payments.
    They can be done by several ways (Paybox, paypal ...)
    """

    class_id = 'payments'
    class_title = MSG(u'Payment history')
    class_handler = PaymentsTable

    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        BooleanCheckBox('payment_ok', title=MSG(u'Payment ok')),
        TextWidget('transaction', title=MSG(u'Id transaction')),
        TextWidget('autorisation', title=MSG(u'Id Autorisation')),
        SelectWidget('status', title=MSG(u'Status')),
        TextWidget('amount', title=MSG(u'Amount')),
        SelectWidget('devise', title=MSG(u'Devise')),
        ]

    # Views
    class_views = ['view', 'configure']

    # List of views
    view = Payments_View()
    #configure = Paybox_Configure()
    #pay = Paybox_Pay()
    #confirm_payment = Paybox_ConfirmPayment()
    #payment_end = Paybox_PaymentEnd()


    @classmethod
    def get_metadata_schema(cls):
        schema = Table.get_metadata_schema()
        # Paybox account configuration
        schema['PBX_SITE'] = String
        schema['PBX_RANG'] = String
        schema['PBX_IDENTIFIANT'] = String
        # Paybox configuration
        schema['PBX_DIFF'] = String
        # Devises
        schema['devise'] = Devises
        return schema


    ######################
    # Public API
    ######################

    def show_payment_form(self, context, payment):
        """
           payment must be a dictionnary with order's identifiant
           and order price.
           For example:
           payment = {'id': 'A250',
                      'price': 250}
        """
        # We check that payment dictionnary is correctly fill.
        if 'id' not in payment or 'price' not in payment:
            raise ValueError, u"Order's id or price is not configure"
        # We show the payment form
        return Paybox_Pay().GET(self, context, payment)



register_resource_class(Payments)
