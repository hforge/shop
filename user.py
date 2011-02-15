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
from itools.datatypes import Boolean, String, Unicode, DateTime
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import SelectRadio, SelectWidget, TextWidget
from ikaaro.forms import BooleanCheckBox
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import Table
from ikaaro.table import OrderedTable, OrderedTableFile
from ikaaro.user import User, UserFolder
from ikaaro.website_views import RegisterForm

# Import from shop
from products.models import get_real_datatype, get_default_widget_shop
from products.enumerate import Datatypes
from user_views import ShopUser_Profile
from user_views import ShopUser_EditAccount, ShopUser_EditGroup
from user_views import ShopUser_AddAddress, ShopUser_EditAddress
from user_views import ShopUser_OrdersView, ShopUser_OrderView
from user_views import Customers_View, AuthentificationLogs_View
from user_views import ShopUser_Manage
from datatypes import UserGroup_Enumerate
from addresses_views import Addresses_Book
from products.dynamic_folder import DynamicFolder
from utils import get_shop, get_group_name
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



class CustomerSchemaTable(OrderedTableFile):

    record_properties = {
        'name': String(unique=True, is_indexed=True),
        'title': Unicode(mandatory=True, multiple=True),
        'mandatory': Boolean,
        'is_public': Boolean,
        'multiple': Boolean,
        'datatype': Datatypes(mandatory=True, index='keyword'),
        'show_on_register': Boolean,
        'default': Unicode,
        }



class CustomerSchema(OrderedTable):

    class_id = 'user-schema'
    class_title = MSG(u'User schema')
    class_version = '20090609'
    class_handler = CustomerSchemaTable
    class_views = ['view', 'add_record']

    form = [
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        BooleanCheckBox('is_public', title=MSG(u'Is public ?')),
        BooleanCheckBox('mandatory', title=MSG(u'Mandatory')),
        BooleanCheckBox('multiple', title=MSG(u'Multiple')),
        BooleanCheckBox('show_on_register', title=MSG(u'Show on register ?')),
        SelectWidget('datatype', title=MSG(u'Data Type')),
        TextWidget('default', title=MSG(u'Default value')),
        ]

    def get_model_schema(self):
        schema = {}
        context = get_context()
        ac = self.get_access_control()
        site_root = context.site_root
        is_admin = ac.is_admin(context.user, site_root)
        get_value = self.handler.get_record_value
        is_on_register_view = issubclass(context.view.__class__, RegisterForm)
        for record in self.handler.get_records_in_order():
            name = get_value(record, 'name')
            show_on_register = get_value(record, 'show_on_register')
            show_on_register = get_value(record, 'show_on_register')
            if is_on_register_view is True and show_on_register is False:
                continue
            is_public = get_value(record, 'is_public')
            if not is_admin and is_public is False:
                continue
            datatype = get_real_datatype(self.handler, record)
            default = get_value(record, 'default')
            if default:
                datatype.default = datatype.decode(default)
            schema[name] = datatype
        return schema


    def get_model_widgets(self):
        context = get_context()
        ac = self.get_access_control()
        site_root = context.site_root
        is_admin = ac.is_admin(context.user, site_root)
        is_on_register_view = issubclass(context.view.__class__, RegisterForm)
        widgets = []
        get_value = self.handler.get_record_value
        for record in self.handler.get_records_in_order():
            name = get_value(record, 'name')
            show_on_register = get_value(record, 'show_on_register')
            if is_on_register_view is True and show_on_register is False:
                continue
            is_public = get_value(record, 'is_public')
            if not is_admin and is_public is False:
                continue
            datatype = get_real_datatype(self.handler, record)
            widget = get_default_widget_shop(datatype)
            title = get_value(record, 'title')
            widget = widget(name, title=title, has_empty_option=False)
            widgets.append(widget)
        return widgets



class Customers(Folder):

    class_id = 'customers'
    class_views = ['view', 'last_connections']

    view = GoToSpecificDocument(
                        title=MSG(u'Customers'),
                        access='is_allowed_to_add',
                        specific_document='/users/')
    last_connections = GoToSpecificDocument(
                        title=MSG(u'Last connections'),
                        access='is_allowed_to_add',
                        specific_document='./authentification_logs')


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        AuthentificationLogs._make_resource(AuthentificationLogs, folder,
                    '%s/authentification_logs' % name, *args, **kw)




class ShopUser(User, DynamicFolder):

    class_version = '20100720'
    class_id = 'user'

    # Views
    manage = ShopUser_Manage()
    profile = ShopUser_Profile()
    edit_account = ShopUser_EditAccount()
    edit_group = ShopUser_EditGroup()

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


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ctime = datetime.now()
        User._make_resource(cls, folder, name, ctime=ctime, *args, **kw)

    base_class_views = ['profile', 'addresses_book', 'edit_account',
                        'orders_view', 'edit_preferences', 'edit_password']

    @property
    def class_views(self):
        context = get_context()
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return ['manage'] + self.base_class_views
        return self.base_class_views


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(DynamicFolder.get_metadata_schema(),
                           cls.base_schema,
                           is_enabled=Boolean,
                           user_group=UserGroup_Enumerate)


    @classmethod
    def get_dynamic_schema(cls):
        context = get_context()
        self = context.resource
        if issubclass(context.view.__class__, RegisterForm):
            group = context.view.get_group(context)
            return group.get_dynamic_schema()
        if not isinstance(self, User):
           self = context.user
        if self is None:
            return {}
        group = self.get_group(context)
        return group.get_dynamic_schema()


    @classmethod
    def get_dynamic_widgets(cls):
        context = get_context()
        self = context.resource
        if issubclass(context.view.__class__, RegisterForm):
            group = context.view.get_group(context)
            return group.get_dynamic_widgets()
        if not isinstance(self, User):
           self = context.user
        if self is None:
            return []
        group = self.get_group(context)
        return group.get_dynamic_widgets()


    def _get_catalog_values(self):
        values = User._get_catalog_values(self)
        values['ctime'] = self.get_property('ctime')
        values['last_time'] = self.get_property('last_time')
        values['user_group'] = str(self.get_property('user_group'))
        values['is_enabled'] = self.get_property('is_enabled')
        return values


    def get_document_types(self):
        return []


    def save_form(self, schema, form):
        dynamic_schema = self.get_dynamic_schema()
        metadata_schema = self.get_metadata_schema()
        for key in schema:
            if key in ['password', 'user_must_confirm']:
                continue
            elif (key not in metadata_schema and
                  key not in dynamic_schema):
                continue
            value = form[key]
            if value is None:
                self.del_property(value)
                continue
            datatype = schema[key]
            if issubclass(datatype, (String, Unicode)):
                value = value.strip()
            self.set_property(key, value)


    def send_register_confirmation(self, context):
        # Get group
        group = self.get_group(context)
        # Get mail subject and body
        subject = group.get_register_mail_subject()
        text = group.get_register_mail_body()
        # Send mail
        context.root.send_email(to_addr=self.get_property('email'),
                                subject=subject, text=text)


    def get_group(self, context):
        shop = get_shop(context.resource)
        group_name = get_group_name(shop, context)
        return shop.get_resource(group_name)


    ###############################################
    ## Update
    ###############################################

    def update_20100719(self):
        if not self.get_property('user_group'):
            self.set_property('user_group', 'default')


    def update_20100720(self):
        ws_name = self.get_root().search(format='shop-neutral').get_documents()[0].name
        group = self.get_property('user_group')
        group = '/%s/shop/groups/%s' % (ws_name, group)
        self.set_property('user_group', group)



class ShopUserFolder(UserFolder):

    class_id = 'users'
    class_views = ['view', 'addresses_book', 'last_connections']
    class_version = '20100823'

    view = Customers_View()
    addresses_book = GoToSpecificDocument(
                        title=MSG(u'Addresses book'),
                        access='is_admin',
                        specific_document='../shop/addresses/')
    last_connections = GoToSpecificDocument(
                        title=MSG(u'Last connections'),
                        access='is_allowed_to_add',
                        specific_document='../shop/customers/authentification_logs')



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

    ###############################################
    ## Update
    ###############################################

    def update_20100719(self):
        cls = CustomerSchema
        cls.make_resource(cls, self, 'public_schema')
        cls.make_resource(cls, self, 'private_schema')


    def update_20100823(self):
        from itools.csv import  Property
        # GEt shop
        root = self.get_root()
        brain = root.search(format='shop').get_documents()[0]
        shop = root.get_resource(brain.abspath)
        # do update
        for name in ['public_schema', 'private_schema']:
            handler = self.get_resource(name).handler
            print handler.key
            for record in handler.get_records():
                kw = {}
                for key, datatype in record.record_properties.items():
                    print key, datatype
                    if key == 'title':
                        value = handler.get_record_value(record, key, 'fr')
                        kw[key] =  Property(value, language='fr')
                    else:
                        kw[key] = handler.get_record_value(record, key)
                value = handler.get_record_value(record, key, 'en')
                kw['is_public'] = name == 'public_schema'
                from pprint import pprint
                pprint(kw)
                groups = ['default']
                if shop.has_pro_price() is True:
                    groups.append('pro')
                for group in groups:
                    group = shop.get_resource('groups/%s/schema' % group)
                    value = handler.get_record_value(record, 'title', 'en')
                    r = group.handler.add_record(kw)
                    kw['title'] =  Property(value, language='en')
                    group.handler.update_record(r.id, **kw)
        self.del_resource('public_schema')
        self.del_resource('private_schema')




register_resource_class(ShopUser)
register_resource_class(ShopUserFolder)
register_resource_class(Customers)
register_resource_class(AuthentificationLogs)

register_field('last_time', DateTime(is_stored=True))
register_field('user_group', String(is_indexed=True))
register_field('is_enabled', Boolean(is_indexed=True))
