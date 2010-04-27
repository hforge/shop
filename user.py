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
from itools.datatypes import Boolean, String, Unicode, DateTime, Tokens
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import BooleanRadio, SelectRadio, SelectWidget, TextWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import Table
from ikaaro.user import User, UserFolder

# Import from shop
from user_views import ShopUser_Profile
from user_views import ShopUser_EditAccount
from user_views import ShopUser_AddAddress, ShopUser_EditAddress
from user_views import ShopUser_OrdersView, ShopUser_OrderView
from user_views import Customers_View, AuthentificationLogs_View
from user_views import ShopUser_EditPrivateInformations, ShopUser_Manage
from user_group import UserGroup_Enumerate
from addresses_views import Addresses_Book
from user_group import groups
from utils import get_shop
from datatypes import Civilite


class AuthentificationLogsBase(BaseTable):

    record_properties = {
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

    class_version = '20091009'
    base_class_views = ['profile', 'addresses_book', 'edit_account',
                        'orders_view', 'edit_preferences', 'edit_password']

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
                              phone1=String(mandatory=True),
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
    private_schema = {'is_enabled': Boolean,
                      'user_group': UserGroup_Enumerate}
    private_widgets = [BooleanRadio('is_enabled', title=MSG(u'Is enabled')),
                       SelectWidget('user_group', title=MSG(u'User group'))]

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ctime = datetime.now()
        User._make_resource(cls, folder, name, ctime=ctime, *args, **kw)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(cls.base_schema,
                           cls.public_schema,
                           cls.private_schema)


    def _get_catalog_values(self):
        values = User._get_catalog_values(self)
        values['ctime'] = self.get_property('ctime')
        values['last_time'] = self.get_property('last_time')
        values['user_group'] = self.get_property('user_group')
        values['is_enabled'] = self.get_property('is_enabled')
        return values


    def get_document_types(self):
        return []


    def get_class_views(self):
        # HACK Virtual
        if self.parent.name == 'customers':
            return ['manage', 'edit_private_informations']
        return self.base_class_views
    class_views = property(get_class_views, None, None, '')


    def save_form(self, schema, form):
        private_schema = self.private_schema
        for key in schema:
            if key in ['password', 'user_must_confirm']:
                continue
            elif (key not in self.get_metadata_schema() and
                  key not in self.get_dynamic_schema() and
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
        context.root.send_email(to_addr=self.get_property('email'),
                                subject=self.mail_subject_template.gettext(),
                                text=self.mail_body_template.gettext())



    ###################################
    ## XXX Dynamic group user
    ###################################
    def get_dynamic_schema(self):
        user_group = self.get_property('user_group')
        if user_group:
            return groups[user_group].schema
        return {}


    def get_property_and_language(self, name, language=None):
        value, language = User.get_property_and_language(self, name,
                                                               language)

        # Default properties first (we need "product_model")
        if name in self.get_metadata_schema():
            return value, language

        # Dynamic property?
        dynamic_schema = self.get_dynamic_schema()
        if name in dynamic_schema:
            datatype = dynamic_schema[name]
            # Default value
            if value is None:
                value = datatype.get_default()
            elif getattr(datatype, 'multiple', False):
                if not isinstance(value, list):
                    # Decode the property
                    # Only support list of strings
                    value = list(Tokens.decode(value))
                # Else a list was already set by "set_property"
            else:
                value = datatype.decode(value)

        return value, language


    def set_property(self, name, value, language=None):
        """Added to handle dynamic properties.
        The value is encoded because metadata won't know about its datatype.
        The multilingual status must be detected to give or not the
        "language" argument.
        """

        # Dynamic property?
        dynamic_schema = self.get_dynamic_schema()
        if name in dynamic_schema:
            datatype = dynamic_schema[name]
            if getattr(datatype, 'multiple', False):
                return User.set_property(self, name,
                                               Tokens.encode(value))
            elif getattr(datatype, 'multilingual', False):
                # If the value equals the default value
                # set the property to None (String's default value)
                # to avoid problems during the language negociation
                if value == datatype.get_default():
                    # XXX Should not be hardcoded
                    # Default value for String datatype is None
                    value = None
                else:
                    value = datatype.encode(value)
                return User.set_property(self, name, value, language)
            # Even if the language was not None, this property is not
            # multilingual so ignore it.
            return User.set_property(self, name,
                                           datatype.encode(value))

        # Standard property
        schema = self.get_metadata_schema()
        datatype = schema[name]
        if getattr(datatype, 'multilingual', False):
            return User.set_property(self, name, value, language)
        return User.set_property(self, name, value)



class ShopUserFolder(UserFolder):


    def set_user(self, email=None, password=None):
        context = get_context()
        shop = get_shop(context.resource)
        # Calculate the user id
        user_id = self.get_next_user_id()
        # Add the user
        cls = shop.user_class
        user = cls.make_resource(cls, self, user_id)
        # Set the email and paswword
        if email is not None:
            user.set_property('email', email)
        if password is not None:
            user.set_password(password)

        # Return the user
        return user


register_resource_class(ShopUser)
register_resource_class(ShopUserFolder)
register_resource_class(Customers)
register_resource_class(AuthentificationLogs)

register_field('last_time', DateTime(is_stored=True))
register_field('user_group', String(is_indexed=True))
register_field('is_enabled', Boolean(is_indexed=True))
