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
from itools.datatypes import Boolean, Unicode, PathDataType, Enumerate
from itools.gettext import MSG


class DeliveryModes(Enumerate):

    options = [{'name': 'weight', 'value': MSG(u'Depends of weight')},
               {'name': 'quantity', 'value': MSG(u'Depends of quantity')}]




delivery_schema = {'title': Unicode,
                   'logo': PathDataType,
                   'description': Unicode,
                   'enabled': Boolean(default=True),
                   'mode': DeliveryModes(default='weight'),
                   'is_free': Boolean}
