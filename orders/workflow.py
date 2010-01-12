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
states = {
  '': MSG(u'Unknow'),
  'open': MSG(u'Waiting payment'),
  'payment_ok': MSG(u'Payment validated'),
  'preparation': MSG(u'Order in preparation'),
  'out_stock': MSG(u'A product is out of stock'),
  'delivery': MSG(u'Package sent'),
  'payment_error': MSG(u'Payment error'),
  'cancel': MSG(u'Canceled'),
  'closed': MSG(u'Closed')}

for name, title in states.items():
    add_state(name, title=title)

states_color = {
  '': None,
  'open': '#BF0000',
  'payment_ok': '#008000',
  'preparation': '#5154FF',
  'out_stock': '#C878D8',
  'delivery': '#FFC500',
  'payment_error': '#FFAB00',
  'cancel': '#FF1F00',
  'closed': '#000000'}


# Transition:
transitions = [
  ('open', 'payment_ok', MSG(u'Validate the payment')),
  ('payment_ok', 'preparation', MSG(u'The order is in preparation')),
  ('payment_ok', 'out_stock', MSG(u'A product is out of stock')),
  ('payment_ok', 'cancel', MSG(u'Cancel the order')),
  ('out_stock', 'preparation', MSG(u'The order is in preparation')),
  ('preparation', 'delivery', MSG(u'Delivery ongoing')),
  ('delivery', 'closed', MSG(u'Closed')),
  ('open', 'payment_error', MSG(u'Signal a payment error')),
  ('payment_error', 'cancel', MSG(u'Cancel the order')),
  ('open', 'cancel', MSG(u'Cancel the order')),
  ('closed', 'open', MSG(u'Re-open the order')),
  ('cancel', 'open', MSG(u'Re-open the order'))]


for before, after, title in transitions:
    add_trans('%s_to_%s' % (before, after), before, after, description=title)

# Define the initial state
order_workflow.set_initstate('open')
