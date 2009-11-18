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
from itools.gettext import MSG
from itools.datatypes import Unicode, String, Email

# Import from ikaaro
from ikaaro import messages
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import AutoForm
from ikaaro.forms import TextWidget, MultilineWidget
from ikaaro.resource_views import EditLanguageMenu
from ikaaro.views_new import NewInstance


supplier_schema = {'title': Unicode(mandatory=True),
                   'address': Unicode(mandatory=True),
                   'phone': String,
                   'fax': String,
                   'email': Email,
                   'description': Unicode}

supplier_widgets = [
        TextWidget('title', title=MSG(u'Title')),
        MultilineWidget('address', title=MSG(u'Address')),
        TextWidget('phone', title=MSG(u'Phone')),
        TextWidget('fax', title=MSG(u'Fax')),
        TextWidget('email', title=MSG(u'Email')),
        MultilineWidget('description', title=MSG(u'Description'))
        ]


class Supplier_Add(NewInstance):

    access = 'is_allowed_to_add'
    title = MSG(u'Add a new supplier')
    schema = merge_dicts(supplier_schema, name=String)
    widgets = [TextWidget('name', title=MSG(u'Name'))] + supplier_widgets

    context_menus = []

    def action(self, resource, context, form):
        from utils import get_shop
        name = form['name']
        # Create the resource
        shop = get_shop(resource)
        resource = shop.get_resource('suppliers')
        cls = shop.supplier_class
        child = cls.make_resource(cls, resource, name)
        # The metadata
        metadata = child.metadata
        language = resource.get_content_language(context)
        for key in supplier_schema:
            metadata.set_property(key, form[key], language=language)

        goto = './%s/' % name
        return context.come_back(messages.MSG_NEW_RESOURCE, goto=goto)



class Supplier_Edit(AutoForm):

    access = 'is_allowed_to_edit'
    title = MSG(u'Edit')
    context_menus = [EditLanguageMenu()]

    schema = supplier_schema

    widgets = supplier_widgets


    def get_value(self, resource, context, name, datatype):
        language = resource.get_content_language(context)
        return resource.get_property(name, language=language)


    def action(self, resource, context, form):
        language = resource.get_content_language(context)
        for key in self.schema.keys():
            resource.set_property(key, form[key], language=language)
        return context.come_back(messages.MSG_CHANGES_SAVED)



class Suppliers_View(Folder_BrowseContent):

    access = 'is_allowed_to_edit'
    title = MSG(u'View')
    context_menus = [EditLanguageMenu()]

    search_template = None

    table_columns = [
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ]

    table_actions = []
