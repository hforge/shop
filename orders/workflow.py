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
from itools.web import get_context
from itools.workflow import Workflow

class Order_Transitions(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        user = context.user
        resource = context.resource
        state = resource.get_state()
        if not state:
            return []
        ac = resource.get_access_control()
        options = []
        for name, trans in state.transitions.items():
            view = resource.get_view(name)
            if ac.is_allowed_to_trans(user, resource, view) is False:
                continue
            description = trans['description'].gettext()
            options.append({'name': name, 'value': description})
        return options


# Workflow definition
order_workflow = Workflow()
add_state = order_workflow.add_state
add_trans = order_workflow.add_trans

# States
add_state('open', title=MSG(u'Open'))
add_state('payment_ok', title=MSG(u'Payment validated'))
add_state('preparation', title=MSG(u'Order in preparation')),
add_state('delivery', title=MSG(u'Delivery ok')),
add_state('payment_error', title=MSG(u'Payment error'))
add_state('cancel', title=MSG(u'Cancel'))
add_state('closed', title=MSG(u'Closed'))


# Transition:
transitions = [
  ('open', 'payment_ok', MSG(u'Validate the payment')),
  ('payment_ok', 'preparation', MSG(u'The order is in preparation')),
  ('preparation', 'delivery', MSG(u'Delivery ongoing')),
  ('delivery', 'closed', MSG(u'Closed')),
  ('open', 'payment_error', MSG(u'Signal a payment error')),
  ('open', 'cancel', MSG(u'Cancel the order')),
  ('closed', 'open', MSG(u'Re-open the order')),
  ('cancel', 'open', MSG(u'Re-open the order'))]


for before, after, title in transitions:
    add_trans('%s_to_%s' % (before, after), before, after, description=title)

# Define the initial state
order_workflow.set_initstate('open')
