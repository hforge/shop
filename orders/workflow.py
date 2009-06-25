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

# Import from itools
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.workflow import Workflow

class Order_States(Enumerate):

    options = [
      {'name': 'waiting',       'value': MSG(u'Waiting for payment')},
      {'name': 'payment_error', 'value': MSG(u'Payment error')},
      {'name': 'preparation',   'value': MSG(u'Order in reparation')},
      {'name': 'cancel',        'value': MSG(u'Canceled')},
      {'name': 'closed',        'value': MSG(u'Closed')},
      {'name': 'delivered',     'value': MSG(u'Delivered')}]


# Workflow definition
order_workflow = Workflow()
add_state = order_workflow.add_state
add_trans = order_workflow.add_trans

# States
for option in Order_States.get_options():
    add_state(option['name'], title=option['value'])

# Transition: Close
add_trans('close', 'waiting', 'closed',
    description=MSG(u'Close order.'))

# Define the initial state
order_workflow.set_initstate('waiting')
