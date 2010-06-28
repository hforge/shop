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
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import Widget, stl_namespaces


class SelectRadioList(Widget):

    template_multiple = list(XMLParser("""
        <ul>
          <li stl:repeat="option options">
            <input type="checkbox" name="${name}" id="${id}-${option/name}"
              value="${option/name}" checked="${option/selected}" />
            <label for="${id}-${option/name}">${option/value}</label>
            <stl:block stl:if="not is_inline"><br/></stl:block>
          </li>
        </ul>
        """, stl_namespaces))

