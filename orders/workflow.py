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
from itools.gettext import MSG
from itools.workflow import Workflow


# Workflow definition
order_workflow = Workflow()
add_state = order_workflow.add_state
add_trans = order_workflow.add_trans
# State: Open
add_state('open', title=MSG(u'Order registered'),
    description=MSG(u'Open'))
# State: Payment validated
add_state('payment_ok', title=MSG(u'Payment validated'),
    description=MSG(u'The payment is validated'))
# State: sended
add_state('sended', title=MSG(u'Sended'),
    description=MSG(u'Order sended'))
# State: Closed
add_state('closed', title=MSG(u'Closed'),
    description=MSG(u'Closed'))
# State: Cancel
add_state('canceled', title=MSG(u'Canceled'),
    description=MSG(u'Canceled'))
# Transition: Cancel
add_trans('cancel', 'open', 'canceled',
    description=MSG(u'Cancel order.'))
# Transition: Close
add_trans('close', 'open', 'closed',
    description=MSG(u'Close order.'))
# Transition: Reopen1
add_trans('reopen1', 'closed', 'open',
    description=MSG(u'Re-open order.'))
# Transition: Repoen2
add_trans('reopen2', 'canceled', 'open',
    description=MSG(u'Re-open order.'))
# Define the initial state
order_workflow.set_initstate('open')
