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
from decimal import Decimal as decimal

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Decimal, Boolean
from itools.gettext import MSG
# Import from ikaaro
from ikaaro.forms import BooleanRadio, TextWidget

# Import from shop
from shop.payments.payment_way_views import PaymentWay_Configure


deposit_schema = {'percent': Decimal(default=decimal('100.0'), mandatory=True),
                  'pay_tax': Boolean(mandatory=True)}

deposit_widgets = [TextWidget('percent', title=MSG(u'Deposit amount (in %)')),
                   BooleanRadio('pay_tax', title=MSG(u'Pay deposite with tax ?'))]


class Deposit_Configure(PaymentWay_Configure):

    title = MSG(u'Configure deposite module')

    schema = merge_dicts(PaymentWay_Configure.schema,
                         deposit_schema)

    widgets = PaymentWay_Configure.widgets + deposit_widgets
