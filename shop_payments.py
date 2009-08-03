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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.registry import register_resource_class

# Import from shop
from payments import Payments


class ShopPayments(Payments):

    class_id = 'shop-payments'
    class_title = MSG(u'Shop payment Module')


    def set_payment_as_ok(self, payment_way, id_record, context):
        shop = self.parent
        # 1) Send Email confirmation
        self.send_confirmation_mail(payment_way, id_record, context)
        # 2) Get corresponding order
        payments_table = payment_way.get_resource('payments').handler
        record = payments_table.get_record(id_record)
        ref = payments_table.get_record_value(record, 'ref')
        order = shop.get_resource('orders/%s' % ref)
        # 3) Set order as payed (so generate bill)
        order.set_as_payed(context)



register_resource_class(ShopPayments)
