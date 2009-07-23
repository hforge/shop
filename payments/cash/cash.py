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

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from shop.payments
from datatypes import RIB, IBAN
from cash_views import CashPayment_Pay, CashPayment_Configure
from shop.payments.payment_way import PaymentWay
from shop.payments.registry import register_payment_way


#from check_views import CheckPayment_RecordEdit
#from check_views import CheckPayment_Pay, CheckPayment_Configure, CheckStates
#from check_views import CheckPayment_RecordAdd, CheckPayment_RecordView



class CashPayment(PaymentWay):

    class_id = 'cash-payment'
    class_title = MSG(u'Payment by cash')
    class_description = MSG(u'Payment by cash')
    class_views = ['configure', 'payments']

    # Views
    configure = CashPayment_Configure()

    # Order admin views
    #order_view = CheckPayment_RecordView()
    #order_add_view = CheckPayment_RecordAdd()
    #order_edit_view = CheckPayment_RecordEdit()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(PaymentWay.get_metadata_schema(),
                           address=Unicode)


    def _show_payment_form(self, context, payment):
        return CashPayment_Pay(conf=payment).GET(self, context)



register_resource_class(CashPayment)
register_payment_way(CashPayment)
