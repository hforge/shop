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
from itools.datatypes import Boolean, Enumerate, String, Unicode
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.forms import BooleanCheckBox, SelectWidget, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTable, OrderedTableFile

# Import from shop
from models_views import ProductModels_View, ProductEnumAttribute_AddRecord


class ProductEnumAttributeTable(OrderedTableFile):

    record_schema = {
        'name': String(Unique=True, index='keyword'),
        'title': Unicode,
        }



class ProductEnumAttribute(OrderedTable):

    class_id = 'product-enum-attribute'
    class_title = MSG(u'Product Enumerate Attribute')
    class_handler = ProductEnumAttributeTable

    add_record = ProductEnumAttribute_AddRecord()

    form = [
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        ]


class AllAttributes(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        model = context.resource.parent
        return [{'name': res.name,
                 'value': res.get_property('title')}
                for res in model.search_resources(cls=ProductEnumAttribute)]



class TableEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        shop = context.resource.parent.parent
        table = cls.model.get_resource(cls.enumerate).handler
        return [{'name': str(table.get_record_value(record, 'name')),
                 'value': table.get_record_value(record, 'title')}
                for record in table.get_records()]



class ProductTypeTable(OrderedTableFile):

    record_schema = {
        'name': String(Unique=True, index='keyword'),
        'title': Unicode,
        'mandatory': Boolean,
        'enumerate': AllAttributes(),
        }



class ProductModelSchema(OrderedTable):

    class_id = 'product-model-schema'
    class_title = MSG(u'Model Schema')
    class_handler = ProductTypeTable


    form = [
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        BooleanCheckBox('mandatory', title=MSG(u'Mandatoy')),
        SelectWidget('enumerate', title=MSG(u'Choice list')),
        ]



class ProductModel(Folder):

    class_id = 'product-model'
    class_title = MSG(u'Product Model')

    __fixed_handlers__ = Folder.__fixed_handlers__ + ['schema']

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        root = Folder._make_resource(cls, folder, name, **kw)
        # Base schema
        ProductModelSchema._make_resource(ProductModelSchema, folder,
                                          '%s/schema' % name,
                                          title={'en': u'Model schema'})


    def get_document_types(self):
        return [ProductEnumAttribute]


    def get_model_schema(self):
        schema = {}
        schema_resource = self.get_resource('schema').handler
        get_value = schema_resource.get_record_value
        for record in schema_resource.get_records():
            enumerate = get_value(record, 'enumerate')
            mandatory = get_value(record, 'mandatory') or False
            datatype = Unicode(mandatory=mandatory)
            if enumerate:
                datatype = TableEnumerate(model=self, enumerate=enumerate,
                                          mandatory=mandatory)
            name = schema_resource.get_record_value(record, 'name')
            schema[name] = datatype
        return schema


    def get_model_widgets(self):
        widgets = []
        schema_resource = self.get_resource('schema').handler
        for record in schema_resource.get_records_in_order():
            widget = TextWidget
            if schema_resource.get_record_value(record, 'enumerate'):
                widget = SelectWidget
            title = schema_resource.get_record_value(record, 'title')
            name = schema_resource.get_record_value(record, 'name')
            widgets.append(widget(name, title=MSG(title)))
        return widgets


    def get_model_ns(self, resource):
        ns = {'specific_dic': {},
              'specific_list': []}
        schema_resource = self.get_resource('schema').handler
        for record in schema_resource.get_records_in_order():
            name = schema_resource.get_record_value(record, 'name')
            title = schema_resource.get_record_value(record, 'title')
            value = resource.get_property(name)
            enumerate = schema_resource.get_record_value(record, 'enumerate')
            if enumerate:
                datatype = TableEnumerate(model=self, enumerate=enumerate)
                value = datatype.get_value(value)
            kw = {'title': title, 'value': value}
            ns['specific_dic'][name] = kw
            ns['specific_list'].append(kw)
        return ns





class ProductModels(Folder):

    class_id = 'product-models'
    class_title = MSG(u'Product Models')
    class_views = ['view']

    view = ProductModels_View()

    def get_document_types(self):
        return [ProductModel]



register_resource_class(ProductModel)
register_resource_class(ProductModelSchema)
register_resource_class(ProductModels)
register_resource_class(ProductEnumAttribute)
