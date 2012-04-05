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
from itools.datatypes import Boolean, String, Unicode, Integer
from itools.datatypes import PathDataType, Decimal, Email, ISOCalendarDate
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import BooleanRadio, BooleanCheckBox, SelectWidget, TextWidget
from ikaaro.forms import XHTMLBody, RTEWidget, get_default_widget
from ikaaro.forms import PathSelectorWidget, ImageSelectorWidget, MultilineWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import OrderedTable, OrderedTableFile

# Import from shop
from enumerate import Datatypes
from models_views import ProductModelSchema_AddRecord
from models_views import ProductModelSchema_EditRecord
from models_views import ProductModelSchema_View
from models_views import ProductModels_View
from models_views import ProductModel_Configure
from shop.datatypes import DatatypeCM_to_INCH, ProductPathDataType
from shop.datatypes import ImagePathDataType, FrenchDate, SIRET_Datatype
from shop.datatypes import PrettyFrenchDate, UnicodeOnePerLine, BigUnicode
from shop.datatypes import ThreeStateBoolean, ShopBoolean
from shop.datatypes import FrenchBirthday_Datatype
from shop.enumerate_table import Enumerate_ListEnumerateTable
from shop.enumerate_table import EnumerateTable_to_Enumerate
from shop.folder import ShopFolder
from shop.forms import ProductSelectorWidget, ThreeStateBooleanRadio
from shop.registry import shop_datatypes
from shop.widgets import FrenchDateWidget, SIRETWidget, RTEWidget_Iframe
from shop.widgets import UnicodeOnePerLineWidget, BirthdayWidget


real_datatypes = {'string': String,
                  'unicode': Unicode,
                  'big-unicode': BigUnicode,
                  'integer': Integer,
                  'decimal': Decimal,
                  'cm_to_inch': DatatypeCM_to_INCH,
                  'boolean': ShopBoolean,
                  'three-state-boolean': ThreeStateBoolean,
                  'path': PathDataType(action='add_link_file'),
                  'image': ImagePathDataType,
                  'product':  ProductPathDataType,
                  'email': Email,
                  'html': XHTMLBody,
                  'html-non-sanitize': XHTMLBody(sanitize_html=False),
                  'unicode-one-per-line': UnicodeOnePerLine,
                  'french-date': FrenchDate,
                  'birthday': FrenchBirthday_Datatype,
                  'pretty-french-date': PrettyFrenchDate,
                  'siret': SIRET_Datatype,
                  'date': ISOCalendarDate}


def get_default_widget_shop(datatype):
    if issubclass(datatype, BigUnicode):
        return MultilineWidget
    elif issubclass(datatype, FrenchBirthday_Datatype):
        return BirthdayWidget
    elif issubclass(datatype, ThreeStateBoolean):
        return ThreeStateBooleanRadio
    elif issubclass(datatype, Boolean):
        return BooleanRadio
    elif issubclass(datatype, FrenchDate):
        return FrenchDateWidget
    elif issubclass(datatype, UnicodeOnePerLine):
        return UnicodeOnePerLineWidget
    elif issubclass(datatype, ProductPathDataType):
        return ProductSelectorWidget
    elif issubclass(datatype, ImagePathDataType):
        return ImageSelectorWidget
    elif issubclass(datatype, PathDataType):
        widget = PathSelectorWidget
        widget.action = datatype.action
        return widget
    elif issubclass(datatype, XHTMLBody):
        if datatype.sanitize_html is False:
            return RTEWidget_Iframe
        return RTEWidget
    elif issubclass(datatype, SIRET_Datatype):
        return SIRETWidget
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
    # Is a registered datatype ?
    for name, title, cls_datatype in shop_datatypes:
        if name == datatype:
            return cls_datatype(**kw)
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
        'datatype': Datatypes(mandatory=True, is_indexed=True, index='keyword'),
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
        TextWidget('name', title=MSG(u'Name')),
        TextWidget('title', title=MSG(u'Title')),
        BooleanCheckBox('mandatory', title=MSG(u'Mandatory')),
        BooleanCheckBox('multiple', title=MSG(u'Multiple')),
        BooleanCheckBox('multilingual', title=MSG(u'Multilingual')),
        BooleanCheckBox('visible', title=MSG(u'Visible')),
        SelectWidget('datatype', title=MSG(u'Data Type')),
        ]


class SpecificModelIs(dict):

    def __getitem__(self, key):
        return key == self.model_name


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


    def _get_catalog_values(self):
        proxy = super(ShopFolder, self)
        values = proxy._get_catalog_values()
        values['declinations_enumerates'] = self.get_property('declinations_enumerates')
        return values


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
        specific_model_is = SpecificModelIs()
        specific_model_is.model_name = self.name
        namespace = {'specific_model_is': specific_model_is,
                     'specific_dict': {},
                     'specific_list': [],
                     'specific_list_complete': []}
        dynamic_schema = self.get_model_schema()
        schema_handler = self.get_resource('schema').handler
        get_value = schema_handler.get_record_value
        for record in schema_handler.get_records_in_order():
            name = get_value(record, 'name')
            value = real_value = resource.get_dynamic_property(name, dynamic_schema)
            # Real value is used to keep the enumerate value
            # corresponding to the options[{'name': xxx}]
            datatype = dynamic_schema[name]
            if value and hasattr(datatype, 'render'):
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

register_field('declinations_enumerates', String(is_indexed=True, multiple=True))
