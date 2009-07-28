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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from shop.payments
from datatypes import RIB, IBAN
from transfer_views import TransferPayment_Configure, TransferPayment_Pay
from transfer_views import TransferPayment_RecordView, TransferPayment_RecordEdit
from shop.payments.payment_way import PaymentWay
from shop.payments.registry import register_payment_way



class TransferPayment(PaymentWay):

    class_id = 'transfer-payment'
    class_title = MSG(u'Payment by transfer')
    class_description = MSG(u'Payment by transfer')
    class_views = ['configure', 'payments']

    logo = '/ui/shop/payments/transfer/images/logo.png'

    # Views
    configure = TransferPayment_Configure()

    # Order admin views
    order_view = TransferPayment_RecordView
    order_edit_view = TransferPayment_RecordEdit

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(PaymentWay.get_metadata_schema(),
                           RIB=RIB,
                           IBAN=IBAN)


    def _show_payment_form(self, context, payment):
        return TransferPayment_Pay(conf=payment).GET(self, context)



register_resource_class(TransferPayment)
register_payment_way(TransferPayment)
