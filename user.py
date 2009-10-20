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

# Import from standard library
from datetime import datetime

# Import from itools
from itools.core import merge_dicts
from itools.csv import Table as BaseTable
from itools.datatypes import String, Unicode, DateTime
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import SelectRadio, TextWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import Table
from ikaaro.user import User

# Import from shop
from addresses_views import Addresses_Book
from datatypes import Civilite
from user_views import ShopUser_Manage, ShopUser_Profile
from user_views import ShopUser_EditAccount
from user_views import ShopUser_AddAddress, ShopUser_EditAddress
from user_views import ShopUser_OrdersView, ShopUser_OrderView
from user_views import Customers_View, AuthentificationLogs_View
from user_views import ShopUser_EditPrivateInformations
from utils import get_shop


class AuthentificationLogsBase(BaseTable):

    record_schema = {
      'user': String(is_indexed=True),
      }


class AuthentificationLogs(Table):

    class_id = 'customers-authentification-logs'
    class_title = MSG(u'Customers authentification logs')
    class_handler = AuthentificationLogsBase
    class_views = ['view']

    view = AuthentificationLogs_View()

    def log_authentification(self, user):
        self.add_new_record({'user': user})



class Customers(Folder):

    class_id = 'customers'
    class_views = ['view', 'last_connections']

    view = Customers_View()
    last_connections = GoToSpecificDocument(
                        title=MSG(u'Last connections'),
                        access='is_allowed_to_add',
                        specific_document='./authentification_logs')


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        AuthentificationLogs._make_resource(AuthentificationLogs, folder,
                    '%s/authentification_logs' % name, *args, **kw)


    def _get_resource(self, name):
        context = get_context()
        is_admin = self.get_access_control().is_admin(context.user, self)
        site_root = self.get_site_root()
        user = site_root.get_resource('/users/' + name, soft=True)
        if user and is_admin:
            return ShopUser(user.metadata)
        return Folder._get_resource(self, name)



class ShopUser(User):

    class_views = ['manage', 'profile', 'addresses_book', 'edit_account',
                   'edit_private_informations', 'orders_view',
                   'edit_preferences', 'edit_password']
    class_version = '20091009'

    # Views
    manage = ShopUser_Manage()
    profile = ShopUser_Profile()
    edit_account = ShopUser_EditAccount()
    edit_private_informations = ShopUser_EditPrivateInformations()

    # Orders views
    orders_view = ShopUser_OrdersView()
    order_view = ShopUser_OrderView()

    # Addresses views
    addresses_book = Addresses_Book(access='is_allowed_to_edit')
    edit_address = ShopUser_EditAddress()
    add_address = ShopUser_AddAddress()


    # Base schema / widgets
    base_schema = merge_dicts(User.get_metadata_schema(),
                              ctime=DateTime,
                              last_time=DateTime,
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

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ctime = datetime.now()
        User._make_resource(cls, folder, name, ctime=ctime, *args, **kw)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(cls.base_schema,
                  cls.public_schema, cls.private_schema)


    def _get_catalog_values(self):
        values = User._get_catalog_values(self)
        values['ctime'] = self.get_property('ctime')
        values['last_time'] = self.get_property('last_time')
        return values


    def get_document_types(self):
        return []


    def save_form(self, schema, form):
        shop = get_shop(self)
        private_schema = shop.user_class.private_schema
        for key in schema:
            if key.startswith('password'):
                continue
            elif (key not in self.get_metadata_schema() and
                  key not in private_schema):
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



    def update_20091009(self):
        from itools.vfs import get_ctime
        t = get_ctime('%s.metadata' % self.handler.uri)
        self.set_property('ctime', t)
        self.set_property('last_time', t)


register_resource_class(ShopUser)
register_resource_class(Customers)
register_resource_class(AuthentificationLogs)

register_field('last_time', DateTime(is_stored=True))
