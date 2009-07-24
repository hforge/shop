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

# Import from itools
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.web import get_context

# Import from payment
from payment_way import PaymentWay

# Import from shop
from shop.utils import get_shop, ShopFolder



# XXX We have to use devises
class Devises(Enumerate):
    """ ISO 4217 """

    options = [
      {'name': '978', 'value': MSG(u'Euro'),   'code': 'EUR', 'symbol': '€'},
      {'name': '840', 'value': MSG(u'Dollar'), 'code': 'USD', 'symbol': '$'},
      ]


class PaymentWaysEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        context = get_context()
        shop = get_shop(context.resource)
        payments = shop.get_resource('payments')
        for mode in payments.search_resources(cls=PaymentWay):
            options.append({'name': mode.name,
                            'value': mode.get_title(),
                            'enabled': mode.get_property('enabled')})
        return options
