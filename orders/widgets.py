# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.web import get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectRadio, stl_namespaces



class OrdersWidget(SelectRadio):

    template = list(XMLParser("""
        <table cellpadding="5" cellspacing="0">
          <tr stl:repeat="option options">
            <td>
              <input type="radio" id="${id}-${option/name}" name="${name}"
                value="${option/name}" checked="checked"
                stl:if="option/selected"/>
              <input type="radio" id="${id}-${option/name}" name="${name}"
                value="${option/name}" stl:if="not option/selected"/>
            </td>
            <td>
              <label for="${id}-${option/name}">
                <span class="counter" style="background-color:${option/color}">
                  ${option/value} <b>${option/count}</b>
                </span>
              </label>
            </td>
          </tr>
        </table>
        """, stl_namespaces))


    def get_namespace(self, datatype, value):
        context = get_context()
        root = context.root
        orders = root.search(format='order')
        proxy = super(OrdersWidget, self)
        namespace = proxy.get_namespace(datatype, value)
        options = []
        for option in namespace['options']:
            nb_items = len(orders.search(workflow_state=option['name']))
            if nb_items == 0:
                continue
            option['count'] = nb_items
            options.append(option)
        namespace['options'] = options
        return namespace
