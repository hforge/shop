# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.core import merge_dicts
from itools.datatypes import String, Unicode

# Import from ikaaro
from ikaaro.registry import register_resource_class
from ikaaro.user import User

# Import from project
from datatypes import Civilite
from user_views import SHOPUser_EditAccount


class ShopUser(User):

    edit_account = SHOPUser_EditAccount()

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(User.get_metadata_schema(),
                           gender=Civilite,
                           phone=String)


    def save_form(self, schema, form):
        for key in schema:
            if key.startswith(('password', 'email')):
                continue
            elif key not in self.get_metadata_schema():
                continue
            value = form[key]
            if value is None:
                self.del_property(value)
                continue
            datatype = schema[key]
            if issubclass(datatype, (String, Unicode)):
                value = value.strip()
            self.set_property(key, value)



register_resource_class(ShopUser)
