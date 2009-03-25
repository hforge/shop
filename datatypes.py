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
from itools.datatypes import Enumerate, String
from itools.gettext import MSG


class StringFixSize(String):

    @classmethod
    def is_valid(cls, value):
        if not value:
            return True
        return len(value) == cls.size


class Civilite(Enumerate):

    options = [
        {'name': 'mister', 'value': MSG(u"M.")},
        {'name': 'madam', 'value': MSG(u"Mme")},
        {'name': 'miss', 'value': MSG(u"Mlle")}]



class UserAddresses(Enumerate):

    @classmethod
    def get_options(cls):
        # Informations
        shop = cls.shop
        user_name = cls.user_name
        addresses = shop.get_resource('addresses').handler
        # Options
        options = []
        for record in addresses.search(user=user_name):
            title = addresses.get_record_value(record, 'title')
            options.append({'name': str(record.id),
                            'value': title})
        return options
