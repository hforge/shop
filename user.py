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
from ikaaro.forms import SelectRadio, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.user import User

# Import from shop
from addresses_views import Addresses_Book
from datatypes import Civilite
from user_views import ShopUser_Profile
from user_views import ShopUser_Manage, ShopUser_EditAccount
from user_views import ShopUser_AddAddress, ShopUser_EditAddress
from user_views import ShopUser_OrdersView, ShopUser_OrderView
from utils import get_shop


class ShopUser(User):

    class_views = ['manage', 'profile', 'addresses_book', 'edit_account',
                   'orders_view', 'edit_preferences', 'edit_password']

    # Views
    # XXX Hide manage view
    manage = ShopUser_Manage()
    profile = ShopUser_Profile()
    edit_account = ShopUser_EditAccount()

    # Orders views
    orders_view = ShopUser_OrdersView()
    order_view = ShopUser_OrderView()

    # Addresses views
    addresses_book = Addresses_Book(access='is_allowed_to_edit')
    edit_address = ShopUser_EditAddress()
    add_address = ShopUser_AddAddress()


    # Base schema / widgets
    base_schema = merge_dicts(User.get_metadata_schema(),
                              gender=Civilite,
                              phone1=String,
                              phone2=String)

    base_widgets = [
                TextWidget('email', title=MSG(u"Email")),
                SelectRadio('gender', title=MSG(u"Civility"), has_empty_option=False),
                TextWidget('lastname', title=MSG(u"Lastname")),
                TextWidget('firstname', title=MSG(u"Firstname")),
                TextWidget('phone1', title=MSG(u"Phone number")),
                TextWidget('phone2', title=MSG(u"Mobile"))]


    # Additional public schema / widgets
    public_schema = {}
    public_widgets = []

    # Additional private schema / widgets
    private_schema = {}
    private_widgets = []


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(cls.base_schema, cls.public_schema)



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
                        subject=self.mail_subject_template,
                        text=self.mail_body_template)


register_resource_class(ShopUser)
