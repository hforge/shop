# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Decimal, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import AutoForm, SelectWidget, TextWidget
from ikaaro.forms import MultilineWidget

# Import from shop
from shop.datatypes import Users_Enumerate


class CreditPayment_View(AutoForm):

    access = 'is_admin'
    title = MSG(u'Add a voucher')

    schema = {'user': Users_Enumerate,
              'amount': Decimal,
              'description': Unicode}

    widgets = [
      SelectWidget('user', title=MSG(u'User')),
      TextWidget('amount', title=MSG(u'Amount (€)')),
      MultilineWidget('description', title=MSG(u'Description'))]


    def action(self, resource, context, form):
        users_credit = resource.get_resource('users-credit').handler
        users_credit.add_record({'user': form['user'],
                                 'amount': form['amount'],
                                 'description': form['description']})
        msg = MSG(u'Voucher has been added !')
        return context.come_back(msg, goto='../')
