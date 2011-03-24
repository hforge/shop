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
from copy import deepcopy
from datetime import datetime

# Import from itools
from itools.core import merge_dicts
from itools.csv import Table as BaseTable
from itools.datatypes import Boolean, String, Unicode, DateTime, Integer
from itools.datatypes import Email
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.uri import Path
from itools.web import get_context
from itools.xapian import AndQuery, PhraseQuery

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import SelectRadio, SelectWidget, TextWidget
from ikaaro.forms import BooleanCheckBox
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import Table
from ikaaro.table import OrderedTable, OrderedTableFile
from ikaaro.user import User, UserFolder
from ikaaro.utils import generate_password
from ikaaro.website_views import RegisterForm

# Import from shop
from csv_views import Export
from datatypes import Civilite
from products.models import get_real_datatype, get_default_widget_shop
from products.enumerate import Datatypes
from user_views import ShopUser_Profile, ShopUser_PublicProfile
from user_views import ShopUser_EditAccount, ShopUser_EditGroup
from user_views import ShopUser_AddAddress, ShopUser_EditAddress
from user_views import ShopUser_OrdersView, ShopUser_OrderView, ShopUser_Viewbox
from user_views import Customers_View, ShopUsers_PublicView, AuthentificationLogs_View
from user_views import ShopUser_Manage
from datatypes import UserGroup_Enumerate
from addresses_views import Addresses_Book
from products.dynamic_folder import DynamicFolder
from utils import get_shop, CurrentFolder_AddImage
from utils import ResourceDynamicProperty
from modules import ModuleLoader


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
        'tip': Unicode,
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
        TextWidget('tip', title=MSG(u'TIP (To show near widget)')),
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
        is_on_register_view = (hasattr(context, 'view') and
                               issubclass(context.view.__class__, RegisterForm))
        for record in self.handler.get_records_in_order():
            name = get_value(record, 'name')
            title = get_value(record, 'title')
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
            datatype.title = title
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
            tip = get_value(record, 'tip')
            widget = widget(name, title=title, has_empty_option=False, tip=tip)
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
    public_profile = ShopUser_PublicProfile()
    edit_account = ShopUser_EditAccount()
    edit_group = ShopUser_EditGroup()
    viewbox = ShopUser_Viewbox()

    # Orders views
    orders_view = ShopUser_OrdersView()
    order_view = ShopUser_OrderView()

    # Addresses views
    addresses_book = Addresses_Book(access='is_allowed_to_edit')
    edit_address = ShopUser_EditAddress()
    add_address = ShopUser_AddAddress()

    add_image = CurrentFolder_AddImage()

    # Base schema / widgets
    base_schema = merge_dicts(User.get_metadata_schema(),
                              lastname=Unicode(title=MSG(u'Lastname')),
                              firstname=Unicode(title=MSG(u'Firstname')),
                              email=Email(title=MSG(u'Email')),
                              ctime=DateTime(title=MSG(u'Register date')),
                              last_time=DateTime(title=MSG(u'Last connection')),
                              gender=Civilite(title=MSG(u"Civility")),
                              phone1=String(mandatory=True, title=MSG(u'Phone1')),
                              phone2=String(title=MSG(u'Phone2')))

    base_widgets = [
                TextWidget('email', title=MSG(u"Email")),
                SelectRadio('gender', title=MSG(u"Civility"), has_empty_option=False),
                TextWidget('lastname', title=MSG(u"Lastname")),
                TextWidget('firstname', title=MSG(u"Firstname")),
                TextWidget('phone1', title=MSG(u"Phone number")),
                TextWidget('phone2', title=MSG(u"Mobile"))]


    base_items = [{'name': 'account',
                   'title': MSG(u"Edit my account"),
                   'href': ';edit_account',
                   'img': '/ui/icons/48x48/card.png'},
                  {'name': 'preferences',
                   'title': MSG(u'Edit my preferences'),
                   'href': ';edit_preferences',
                   'img': '/ui/icons/48x48/preferences.png'},
                  {'name': 'password',
                   'title': MSG(u'Edit my password'),
                   'href': ';edit_password',
                   'img': '/ui/icons/48x48/lock.png'},
                  {'name': 'addresses',
                   'title': MSG(u'My addresses book'),
                   'href': ';addresses_book',
                   'img': '/ui/icons/48x48/tasks.png'},
                  {'name': 'orders',
                   'title': MSG(u'Orders history'),
                   'href': ';orders_view',
                   'img': '/ui/shop/images/bag_green.png'}]


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
        if hostname[:6] == 'www.aw':
            # XXX Add a configurator for public profil
            return ['public_profile'] + self.base_class_views
        return self.base_class_views


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(
            DynamicFolder.get_metadata_schema(),
            cls.base_schema,
            is_enabled=Boolean(title=MSG(u'Enabled')),
            user_group=UserGroup_Enumerate(title=MSG(u'Group')))


    @classmethod
    def get_dynamic_schema(cls):
        context = get_context()
        self = context.resource
        if (hasattr(context, 'view') and
            issubclass(context.view.__class__, RegisterForm)):
            group = context.view.get_group(context)
            return group.get_dynamic_schema()
        if not isinstance(self, User):
           self = context.user
        if self is None:
            group = context.site_root.get_resource('shop/groups/default')
        else:
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


    def get_public_title(self):
        return self.get_dynamic_property('pseudo')


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


    confirmation_txt = MSG(u"To confirm your identity, click the link:"
                           u"\n"
                           u"\n {uri}")

    def send_register_confirmation(self, context, need_email_validation=False):
        # Get group
        group = self.get_group(context)
        # Get mail subject and body
        subject = group.get_register_mail_subject()
        text = group.get_register_mail_body()
        # Registration need validation ?
        if need_email_validation:
            key = generate_password(30)
            self.set_property('user_must_confirm', key)
            # Build the confirmation link
            confirm_url = deepcopy(context.uri)
            path = '/users/%s/;confirm_registration' % self.name
            confirm_url.path = Path(path)
            confirm_url.query = {'key': key, 'username': self.get_login_name()}
            confirm_url = str(confirm_url)
            text += '\n\n'
            text += self.confirmation_txt.gettext(uri=confirm_url)

        # Send mail
        context.root.send_email(to_addr=self.get_property('email'),
                                subject=subject, text=text)


    def get_group(self, context):
        user_group = self.get_property('user_group')
        return context.root.get_resource(user_group)


    def to_text(self):
        texts = []
        for key, datatype in (self.get_dynamic_schema().items() +
                              self.get_metadata_schema().items()):
            if key == 'password':
                continue
            value = self.get_property(key)
            if value:
                value = datatype.encode(value)
                value = unicode(value, 'utf-8')
                texts.append(value)
        return u'\n'.join(texts)


    def get_namespace(self, context):
        root = context.root
        # Get dynamic user values
        dynamic_user_value = ResourceDynamicProperty()
        dynamic_user_value.schema = self.get_dynamic_schema()
        dynamic_user_value.resource = self
        # Module
        shop_module = ModuleLoader()
        shop_module.context = context
        shop_module.here = self
        # Get modules items
        modules_items = []
        search = context.root.search(is_shop_user_module=True)
        for brain in search.get_documents():
            shop_user_module = root.get_resource(brain.abspath)
            modules_items.append(
                {'name': shop_user_module.element_name,
                 'title': shop_user_module.element_title,
                 'href': shop_user_module.element_name,
                 'img': shop_user_module.class_icon48})
        # Ctime
        ctime = self.get_property('ctime')
        accept = context.accept_language
        # ACLS
        ac = self.get_access_control()
        is_authenticated = ac.is_authenticated(context.user, self)
        is_owner = context.user is not None and context.user.name == self.name
        # Build namespace
        return {'name': self.name,
                'link': context.get_link(self),
                'module': shop_module,
                'dynamic_user_value': dynamic_user_value,
                'is_owner': is_owner,
                'is_authenticated': is_authenticated,
                'ctime': format_datetime(ctime, accept) if ctime else None, # XXX Why ?
                'items': self.base_items + modules_items}

    ###############################
    # Computed schema
    ###############################
    computed_schema = {'nb_orders': Integer(title=MSG(u'Nb orders (even cancel)')),
                       'address': Unicode(title=MSG(u'Last known user address'))}

    @property
    def nb_orders(self):
        # XXX Orders states
        root = self.get_root()
        queries = [PhraseQuery('format', 'order'),
                   PhraseQuery('customer_id', self.name)]
        return len(root.search(AndQuery(*queries)))


    @property
    def address(self):
        # XXX We should have a default address ?
        context = get_context()
        shop = get_shop(context.resource)
        addresses_h = shop.get_resource('addresses').handler
        records = addresses_h.search(user=self.name)
        if len(records) == 0:
            return None
        record = records[0]
        addresse = addresses_h.get_record_namespace(record.id)
        addr = u''
        for key in ['address_1', 'address_2', 'zipcode', 'town', 'country']:
            try:
                addr += u'%s ' % addresse[key]
            except Exception:
                # XXX Why ?
                addr += u'XXX'
        return addr



class ShopUserFolder(UserFolder):

    class_id = 'users'
    class_version = '20100823'
    backoffice_class_views = ['view', 'addresses_book', 'last_connections'], #'export']

    @property
    def class_views(self):
        context = get_context()
        # Back-Office
        hostname = context.uri.authority
        if hostname[:6] == 'admin.' :
            return self.backoffice_class_views
        if hostname[:6] == 'www.aw':
            # XXX Add a configurator for public profil
            return ['public_view']
        return []


    view = Customers_View()
    public_view = ShopUsers_PublicView()
    addresses_book = GoToSpecificDocument(
                        title=MSG(u'Addresses book'),
                        access='is_admin',
                        specific_document='../shop/addresses/')
    last_connections = GoToSpecificDocument(
                        title=MSG(u'Last connections'),
                        access='is_allowed_to_add',
                        specific_document='../shop/customers/authentification_logs')

    #############################
    # Export
    #############################

    export = Export(
        export_resource=ShopUser,
        access='is_allowed_to_edit',
        file_columns=['name', 'is_enabled', 'user_group', 'gender',
                      'firstname', 'lastname', 'email', 'phone1',
                      'phone2', 'address', 'nb_orders', 'ctime'])

    #############################
    # Api
    #############################

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
