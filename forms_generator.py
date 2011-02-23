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
from itools.datatypes import Email, Enumerate, Unicode, Boolean, String
from itools.gettext import MSG
from itools.uri import get_reference
from itools.web import get_context
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import AutoForm, SelectWidget, TextWidget, BooleanCheckBox
from ikaaro.forms import RTEWidget, XHTMLBody
from ikaaro.table import OrderedTable, OrderedTableFile
from ikaaro.table_views import OrderedTable_View

# Import from itws
from itws.views import AutomaticEditView

# Import from shop
from cross_selling_views import AddProduct_View
from datatypes import ProductPathDataType
from products.models import get_real_datatype
from products.enumerate import Datatypes
from registry import shop_widgets
from utils import get_shop


class Widgets(Enumerate):


    @classmethod
    def get_options(cls):
        options = []
        for name, title, widget in shop_widgets:
            options.append({'name': name, 'value': title})
        return options


    @classmethod
    def get_widget(cls, widget_name):
        for name, title, widget in shop_widgets:
            if name == widget_name:
                return widget
        raise ValueError



class ShopForm_Display(AutoForm):

    access = True


    def get_submit_value(self):
        context = get_context()
        return context.resource.get_property('submit_value')

    submit_value = property(get_submit_value, None, None, '')



    def get_title(self, context):
        return context.resource.get_title()


    def get_value(self, resource, context, name, datatype):
        return context.query.get(name) or datatype.get_default()


    def get_namespace(self, resource, context):
        namespace = AutoForm.get_namespace(self, resource, context)
        namespace['required_msg'] = (resource.get_property('introduction') +
                                     list(XMLParser('<br/><br/>')) +
                                     list(namespace['required_msg']))
        return namespace


    def get_schema(self, resource, context):
        schema = {}
        handler = resource.handler
        get_value = handler.get_record_value
        for record in handler.get_records():
            name = get_value(record, 'name')
            datatype = get_real_datatype(handler, record)
            datatype.name = name
            schema[name] = datatype
        return schema


    def get_query_schema(self):
        context = get_context()
        resource = context.resource
        schema = {}
        for key, datatype in self.get_schema(resource, context).items():
            datatype.mandatory = False
            schema[key] = datatype
        return schema


    def get_widgets(self, resource, context):
        widgets = []
        handler = resource.handler
        get_value = handler.get_record_value
        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            widget = Widgets.get_widget(get_value(record, 'widget'))
            title = get_value(record, 'title')
            widget = widget(name, title=title, has_empty_option=False)
            widgets.append(widget)
        return widgets


    def action(self, resource, context, form):
        root = context.root
        to_addr = resource.get_property('to_addr')
        subject = MSG(u'Message from form: "%s"' % resource.get_title()).gettext()
        text = []
        handler = resource.handler
        get_value = handler.get_record_value
        from_addr = to_addr
        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            datatype = get_value(record, 'datatype')
            value = form[name]
            # XXX Render on datatype ?
            if datatype == 'product':
                shop = get_shop(resource)
                site_root = resource.get_site_root()
                product = context.root.get_resource(value)
                base_uri = shop.get_property('shop_uri')
                end_uri = site_root.get_pathto(product)
                value = get_reference(base_uri).resolve(end_uri)
            elif datatype == 'email':
                # XXX Set from_addr
                from_addr = value
            title = get_value(record, 'title')
            text.append('*%s* \n\n %s' % (title, value))
        text = '\n\n\n'.join(text)
        root.send_email(to_addr, subject, from_addr=from_addr, text=text,
                        subject_with_host=False)
        return resource.get_property('final_message')



class ShopFormTable(OrderedTableFile):

    record_properties = {
        'name': String,
        'title': Unicode(mandatory=True, multiple=True),
        'mandatory': Boolean,
        'multiple': Boolean,
        'datatype': Datatypes(mandatory=True, index='keyword'),
        'widget': Widgets(mandatory=True),
        }


class ShopForm(OrderedTable):

    class_id = 'shop-form'
    class_title = MSG(u'Shop form')
    class_version = '20090609'
    class_handler = ShopFormTable
    class_views = ['display', 'edit'] # 'view', 'add_record'] #XXX We hide for instant

    display = ShopForm_Display()
    view = OrderedTable_View(search_template=None)
    edit = AutomaticEditView()

    add_product = AddProduct_View()

    form = [
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        BooleanCheckBox('mandatory', title=MSG(u'Mandatory')),
        BooleanCheckBox('multiple', title=MSG(u'Multiple')),
        SelectWidget('datatype', title=MSG(u'Data Type')),
        SelectWidget('widget', title=MSG(u'Widget')),
        ]

    edit_widgets = [TextWidget('submit_value', title=MSG(u'Submit value')),
                    TextWidget('to_addr', title=MSG(u'To addr')),
                    RTEWidget('introduction', title=MSG(u'Introduction')),
                    RTEWidget('final_message', title=MSG(u'Final message'))]

    edit_schema = {'submit_value': Unicode(multilingual=True, mandatory=True),
                   'to_addr': Email(mandatory=True),
                   'introduction': XHTMLBody(multilingual=True),
                   'final_message': XHTMLBody(multilingual=True)}

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(OrderedTable.get_metadata_schema(),
                           cls.edit_schema)
