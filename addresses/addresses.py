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
from itools.csv import Table as BaseTable
from itools.datatypes import Unicode, String
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import TextWidget, MultilineWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table


class BaseAddresses(BaseTable):

    record_schema = {
      'user': String,
      'address_1': Unicode(mandatory=True),
      'address_2': Unicode(),
      'zipcode': String(mandatory=True),
      'town': Unicode(mandatory=True),
      'country': Unicode(mandatory=True),
      }



class Addresses(Table):

    class_id = 'addresses'
    class_title = MSG(u'Adresse')
    class_handler = BaseAddresses

    form = [
        TextWidget('user', title=MSG(u'User')),
        TextWidget('address_1', title=MSG(u'Address')),
        TextWidget('address_2', title=MSG(u'Address (next)')),
        TextWidget('zipcode', title=MSG(u'Zip Code')),
        TextWidget('town', title=MSG(u'Town')),
        TextWidget('country', title=MSG(u'Country')),
        ]


register_resource_class(Addresses)
