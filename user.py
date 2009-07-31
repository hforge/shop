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
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.registry import register_resource_class
from ikaaro.user import User

# Import from shop
from datatypes import Civilite
from user_views import ShopUser_Manage, SHOPUser_EditAccount
from utils import get_shop


class ShopUser(User):

    class_views = ['manage', 'profile', 'edit_account',
                   'my_orders', 'edit_preferences', 'edit_password']

    # Views
    manage = ShopUser_Manage()
    edit_account = SHOPUser_EditAccount()
    my_orders = GoToSpecificDocument(specific_document='../../shop/orders',
                     icon='tasks.png', title=MSG(u'My orders'),
                     description=MSG(u'Orders history in the shop'))

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(User.get_metadata_schema(),
                           gender=Civilite,
                           phone1=String,
                           phone2=String)


    def save_form(self, schema, form):
        for key in schema:
            if key.startswith('password'):
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


    mail_subject_template = MSG(u"Inscription confirmation.")
    mail_body_template = MSG(u"Your inscription has been validated")


    def send_register_confirmation(self, context):
        shop = get_shop(context.resource)
        shop.send_email(context,
                        to_addr=self.get_property('email'),
                        subject=self.mail_subject_template.gettext(),
                        text=self.mail_body_template.gettext(),
                        send_in_html=True)


register_resource_class(ShopUser)
