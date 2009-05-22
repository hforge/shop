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
from itools.core import merge_dicts
from itools.datatypes import String, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.forms import SelectRadio, SelectWidget
from ikaaro.forms import TextWidget, PasswordWidget
from ikaaro.messages import MSG_CHANGES_SAVED
from ikaaro.user_views import User_EditAccount
from ikaaro.website_views import RegisterForm

# Import from shop
from countries import CountriesEnumerate
from datatypes import Civilite


user_schema = merge_dicts(RegisterForm.schema,
                          gender=Civilite(mandatory=True),
                          password=String(mandatory=True),
                          password_check=String(mandatory=True),
                          phone1=String,
                          phone2=String,
                          address_1=Unicode(mandatory=True),
                          address_2=Unicode,
                          zipcode=String(mandatory=True),
                          town=Unicode(mandatory=True),
                          country=CountriesEnumerate(mandatory=True))


user_widgets = [TextWidget('email', title=MSG(u"Email")),
                SelectRadio('gender', title=MSG(u"Civility"), has_empty_option=False),
                TextWidget('lastname', title=MSG(u"Lastname")),
                TextWidget('firstname', title=MSG(u"Firstname")),
                PasswordWidget('password', title=MSG(u"Password")),
                PasswordWidget('password_check', title=MSG(u"Repeat password")),
                TextWidget('phone1', title=MSG(u"Phone number")),
                TextWidget('phone2', title=MSG(u"Mobile")),
                TextWidget('address_1', title=MSG(u"Address")),
                TextWidget('address_2', title=MSG(u"Address")),
                TextWidget('zipcode', title=MSG(u"Zip code")),
                TextWidget('town', title=MSG(u"Town")),
                SelectWidget('country', title=MSG(u"Pays"))]



class SHOPUser_EditAccount(User_EditAccount):

    def get_schema(self, resource, context):
        return user_schema


    def get_widgets(self, resource, context):
        return user_widgets


    def get_value(self, resource, context, name, datatype):
        if name == 'password':
            return None
        return resource.get_property(name) or datatype.get_default()


    def action(self, resource, context, form):
        # Save changes
        schema = self.get_schema(resource, context)
        resource.save_form(schema, form)
        # Message 
        context.message = MSG_CHANGES_SAVED
