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
from itools.datatypes import Boolean, Enumerate, String, Unicode, Integer
from itools.datatypes import PathDataType, Decimal, Email, ISOCalendarDate
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import BooleanRadio, BooleanCheckBox, SelectWidget, TextWidget
from ikaaro.forms import XHTMLBody, RTEWidget, get_default_widget
from ikaaro.forms import PathSelectorWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTable, OrderedTableFile

# Import from shop
from enumerate import Datatypes
from models_views import ProductModelSchema_AddRecord
from models_views import ProductModelSchema_EditRecord
from models_views import ProductModelSchema_View
from models_views import ProductModels_View
from models_views import ProductModel_Configure
from shop.datatypes import DatatypeCM_to_INCH, ProductPathDataType
from shop.enumerate_table import Enumerate_ListEnumerateTable
from shop.enumerate_table import EnumerateTable_to_Enumerate
from shop.folder import ShopFolder
from shop.forms import ProductSelectorWidget


real_datatypes = {'string': String,
                  'unicode': Unicode,
                  'integer': Integer,
                  'decimal': Decimal,
                  'cm_to_inch': DatatypeCM_to_INCH,
                  'boolean': Boolean,
                  'path': PathDataType,
                  'product':  ProductPathDataType,
                  'email': Email,
                  'html': XHTMLBody,
                  'date': ISOCalendarDate}



class LinkPathSelectorWidget(PathSelectorWidget):

    action = 'add_link_file'



def get_default_widget_shop(datatype):
    if issubclass(datatype, Boolean):
        return BooleanRadio
    elif issubclass(datatype, ProductPathDataType):
        return ProductSelectorWidget
    elif issubclass(datatype, PathDataType):
        return LinkPathSelectorWidget
    elif issubclass(datatype, XHTMLBody):
        return RTEWidget
    return get_default_widget(datatype)


def get_real_datatype(schema_handler, record):
    # If name not in real_datatypes dict ...
    # It's an enumerate table from enumerates library
    # that we transform in Enumerate
    get_value = schema_handler.get_record_value
    datatype = get_value(record, 'datatype')
    # Get properties
    kw = {}
    for key in ['mandatory', 'multiple', 'multilingual']:
        kw[key] = get_value(record, key)
    # Get real datatype from real_datatypes dict
    if real_datatypes.has_key(datatype):
        return real_datatypes[datatype](**kw)
    # It's an TableEnumerate
    kw['enumerate_name'] = get_value(record, 'datatype')
    return EnumerateTable_to_Enumerate(**kw)



class ProductTypeTable(OrderedTableFile):

    record_properties = {
        # XXX To remove
        'name': String(unique=True, is_indexed=True),
        'title': Unicode(mandatory=True, multiple=True),
        'mandatory': Boolean,
        'multiple': Boolean,
        'multilingual': Boolean,
        'visible': Boolean,
        # XXX To remove
        'is_purchase_option': Boolean,
        'datatype': Datatypes(mandatory=True, index='keyword'),
        }



class ProductModelSchema(OrderedTable):

    class_id = 'product-model-schema'
    class_title = MSG(u'Model Schema')
    class_version = '20090609'
    class_handler = ProductTypeTable
    class_views = ['view', 'add_record']

    view = ProductModelSchema_View()
    add_record = ProductModelSchema_AddRecord()
    edit_record = ProductModelSchema_EditRecord()

    form = [
        TextWidget('title', title=MSG(u'Title')),
        BooleanCheckBox('mandatory', title=MSG(u'Mandatory')),
        BooleanCheckBox('multiple', title=MSG(u'Multiple')),
        BooleanCheckBox('multilingual', title=MSG(u'Multilingual')),
        BooleanCheckBox('visible', title=MSG(u'Visible')),
        SelectWidget('datatype', title=MSG(u'Data Type')),
        ]

    #########################
    # Update methods
    #########################

    def update_20090414(self):
        handler = self.handler
        for record in handler.get_records():
            handler.update_record(record.id, datatype='unicode')


    def update_20090609(self):
        handler = self.handler
        for record in handler.get_records():
            if handler.get_record_value(record, 'datatype') == 'enumerate':
                enumerate = handler.get_record_value(record, 'enumerate')
                handler.update_record(record.id, datatype=enumerate)



class ProductModel(ShopFolder):

    class_id = 'product-model'
    class_title = MSG(u'Product Model')
    class_views = ['configure', 'view']

    view = GoToSpecificDocument(specific_document='schema',
                                title=MSG(u'View model details'))
    configure = ProductModel_Configure()

    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['schema']


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                declinations_enumerates=Enumerate_ListEnumerateTable(multiple=True))


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        root = ShopFolder._make_resource(cls, folder, name, **kw)
        # Base schema
        ProductModelSchema._make_resource(ProductModelSchema, folder,
                                          '%s/schema' % name,
                                          title={'en': u'Model schema'})


    def get_document_types(self):
        return []


    def get_model_schema(self):
        schema = {}
        schema_resource = self.get_resource('schema')
        schema_handler = schema_resource.handler
        get_value = schema_handler.get_record_value
        for record in schema_handler.get_records_in_order():
            name = get_value(record, 'name')
            schema[name] = get_real_datatype(schema_handler, record)
        return schema


    def get_model_widgets(self):
        widgets = []
        schema_handler = self.get_resource('schema').handler
        get_value = schema_handler.get_record_value
        for record in schema_handler.get_records_in_order():
            name = get_value(record, 'name')
            datatype = get_real_datatype(schema_handler, record)
            widget = get_default_widget_shop(datatype)
            title = get_value(record, 'title')
            widget = widget(name, title=title, has_empty_option=False)
            widgets.append(widget)
        return widgets


    def get_model_namespace(self, resource):
        context = get_context()
        namespace = {'specific_dict': {},
                     'specific_list': [],
                     'specific_list_complete': []}
        schema_handler = self.get_resource('schema').handler
        get_value = schema_handler.get_record_value
        for record in schema_handler.get_records_in_order():
            name = get_value(record, 'name')
            value = real_value = resource.get_property(name)
            # Real value is used to keep the enumerate value
            # corresponding to the options[{'name': xxx}]
            datatype = get_real_datatype(schema_handler, record)
            # XXX Use datatype.render()
            if issubclass(datatype, Enumerate):
                if datatype.multiple:
                    values = [datatype.get_value(x) for x in real_value]
                    value = ', '.join(values)
                else:
                    value = datatype.get_value(real_value)
            # XXX Use datatype.render()
            if issubclass(datatype, Boolean):
                if value:
                    value = MSG(u'Yes')
                else:
                    value = MSG(u'No')
            if hasattr(datatype, 'render'):
                value = datatype.render(value, context)
            # Build kw
            kw = {'value': value,
                  'real_value': real_value}
            for key in ['name', 'title', 'multiple', 'visible']:
                kw[key] = get_value(record, key)
            # Add to namespace
            namespace['specific_dict'][name] = kw
            namespace['specific_list_complete'].append(kw)
            if kw['visible'] and kw['value']:
                namespace['specific_list'].append(kw)
        return namespace




class ProductModels(ShopFolder):

    class_id = 'product-models'
    class_title = MSG(u'Product Models')
    class_views = ['browse_content', 'new_resource?type=product-model']

    # Views
    browse_content = ProductModels_View()


    def get_document_types(self):
        return [ProductModel]



register_resource_class(ProductModel)
register_resource_class(ProductModelSchema)
register_resource_class(ProductModels)
