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
from ikaaro.forms import SelectRadio, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.datatypes import Civilite


class BaseAddresses(BaseTable):

    record_schema = {
      'title': Unicode(index='keyword'),
      'gender': Civilite,
      'firstname': Unicode,
      'lastname': Unicode,
      'user': String(index='keyword'),
      'address_1': Unicode(mandatory=True),
      'address_2': Unicode,
      'zipcode': String(mandatory=True),
      'town': Unicode(mandatory=True),
      'country': Unicode(mandatory=True),
      }



class Addresses(Table):

    class_id = 'addresses'
    class_title = MSG(u'Adresse')
    class_handler = BaseAddresses

    form = [
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('user', title=MSG(u'User')),
        SelectRadio('gender', title=MSG(u'Genre')),
        TextWidget('firstname', title=MSG(u'Firstname')),
        TextWidget('lastname', title=MSG(u'Lastname')),
        TextWidget('address_1', title=MSG(u'Address')),
        TextWidget('address_2', title=MSG(u'Address (next)')),
        TextWidget('zipcode', title=MSG(u'Zip Code')),
        TextWidget('town', title=MSG(u'Town')),
        TextWidget('country', title=MSG(u'Country')),
        ]


register_resource_class(Addresses)
