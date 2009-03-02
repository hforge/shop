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
from itools.csv import Table as BaseTable
from itools.datatypes import Boolean, Decimal, Enumerate, String, Tokens, Unicode
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table
from ikaaro.table import OrderedTable, OrderedTableFile

# Import from shop
from product_views import Product_View, Product_Edit, Product_Images
from schema import product_schema


class AllAttributes(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        attributes = root.get_resource('attributes')
        return [{'name': res.name,
                 'value': res.get_property('title')}
                for res in attributes.get_resources()]



class TableEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        root = context.root
        table = root.get_resource('attributes/%s' % cls.name).handler
        return [{'name': str(table.get_record_value(record, 'name')),
                 'value': table.get_record_value(record, 'title')}
                for record in table.get_records()]



class ProductTypeTable(OrderedTableFile):

    record_schema = {
        'name': String(Unique=True, index='keyword'),
        'title': Unicode(),
        'enumerate': AllAttributes(),
        }



class ProductType(OrderedTable):

    class_id = 'product-type'
    class_title = MSG(u'Product type')
    class_handler = ProductTypeTable


    form = [
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        SelectWidget('enumerate', title=MSG(u'Enumerate')),
        ]


    def get_producttype_schema(self):
        schema = {}
        for record in self.handler.get_records():
            datatype = Unicode
            enumerate = self.handler.get_record_value(record, 'enumerate')
            if enumerate:
                datatype = TableEnumerate(name=enumerate)
            name = self.handler.get_record_value(record, 'name')
            schema[name] = datatype
        return schema


    def get_producttype_widgets(self):
        widgets = []
        for record in self.handler.get_records_in_order():
            widget = TextWidget
            if self.handler.get_record_value(record, 'enumerate'):
                widget = SelectWidget
            title = self.handler.get_record_value(record, 'title')
            name = self.handler.get_record_value(record, 'name')
            widgets.append(widget(name, title=MSG(title)))
        return widgets


    def get_producttype_ns(self, resource):
        ns = {'specific_dic': {},
              'specific_list': []}
        for record in self.handler.get_records_in_order():
            name = self.handler.get_record_value(record, 'name')
            title = self.handler.get_record_value(record, 'title')
            value = resource.get_property(name)
            enumerate = self.handler.get_record_value(record, 'enumerate')
            if enumerate:
                datatype = TableEnumerate(name=enumerate)
                value = datatype.get_value(value)
            kw = {'title': title, 'value': value}
            ns['specific_dic'][name] = kw
            ns['specific_list'].append(kw)
        return ns



class ProductTypes(Folder):

    class_id = 'product-types'
    class_title = MSG(u'Product types')


    def get_document_types(self):
        return [ProductType]



register_resource_class(ProductType)
register_resource_class(ProductTypes)
