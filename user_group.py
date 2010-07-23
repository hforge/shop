# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Boolean, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.buttons import RemoveButton, RenameButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import BooleanRadio, MultilineWidget, TextWidget
from ikaaro.webpage import WebPage

# Import from itws
from itws.views import AutomaticEditView

# Import from shop
from folder import ShopFolder
from shop_views import Shop_Register
from user import CustomerSchema


class Group_Register(Shop_Register):

    def get_group_abspath(self, context):
        return str(context.resource.get_abspath())


    def get_group_schema(self, context):
        schema = context.resource.get_resource('schema')
        return schema.get_model_schema()


    def get_group_widgets(self, context):
        schema = context.resource.get_resource('schema')
        return schema.get_model_widgets()


    def get_user_is_enabled(self, resource):
        return resource.get_property('user_is_enabled_when_register')




class ShopUser_Group(ShopFolder):

    class_id = 'user-group'
    class_views = ['edit', 'register']
    class_version = '20100719'
    class_title = MSG(u'User group')

    edit = AutomaticEditView()
    register = Group_Register()

    edit_schema = {'register_mail_subject': Unicode(multilingual=True),
                   'register_mail_body': Unicode(multilingual=True),
                   'user_is_enabled_when_register': Boolean,
                   'show_ht_price': Boolean}

    edit_widgets = [TextWidget('register_mail_subject', title=MSG(u'Register mail subject')),
                    MultilineWidget('register_mail_body', title=MSG(u'Register mail body')),
                    BooleanRadio('user_is_enabled_when_register', title=MSG(u'User is enabled ?')),
                    BooleanRadio('show_ht_price', title=MSG(u'Show HT price ?'))]



    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['welcome']


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create group
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        # Group schema
        cls = CustomerSchema
        cls._make_resource(cls, folder, '%s/schema' % name)
        # Welcome Page
        cls = WebPage
        cls._make_resource(cls, folder, '%s/welcome' % name,
                                title={'en': u'Welcome'},
                                state='public')

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           cls.edit_schema)


    def get_register_mail_subject(self):
        subject = self.get_property('register_mail_subject')
        if subject:
            return subject
        return MSG(u"Inscription confirmation.").gettext()


    def get_register_mail_body(self):
        body = self.get_property('register_mail_body')
        if body:
            return body
        return MSG(u"Your inscription has been validated").gettext()


    def update_20100719(self):
        cls = CustomerSchema
        cls.make_resource(cls, self, 'schema')



class Groups_View(Folder_BrowseContent):

    search_template = None

    table_actions = [RemoveButton, RenameButton]
    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ]



class ShopUser_Groups(ShopFolder):

    class_id = 'user-groups'
    class_title = MSG(u'User groups')
    class_version = '20100720'
    class_views = ['view']

    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['default']

    view = Groups_View()

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        ShopUser_Group._make_resource(ShopUser_Group, folder, '%s/default' % name)


    def get_document_types(self):
        return [ShopUser_Group]


    def update_20100720(self):
        cls = ShopUser_Group
        kw = {'user_is_enabled_when_register': True}
        cls.make_resource(cls, self, 'default', **kw)
